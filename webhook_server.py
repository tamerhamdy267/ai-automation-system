import os
import re
import uuid
import time
from datetime import datetime

from flask import Flask, request, jsonify, render_template, redirect, Response
from dotenv import load_dotenv

from ai_classifier import run_automation
from database import get_pending_escalations
from database import resolve_escalation
from database import is_message_processed
from database import mark_message_processed
from database import initialize_database

initialize_database()

load_dotenv()

API_KEY = os.getenv("AI_API_KEY")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def require_admin_auth():

    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return Response(
            "Admin authentication is not configured.",
            status=503
        )

    auth = request.authorization

    if (
        not auth
        or auth.username != ADMIN_USERNAME
        or auth.password != ADMIN_PASSWORD
    ):
        return Response(
            "Authentication required.",
            status=401,
            headers={
                "WWW-Authenticate": 'Basic realm="AI Automation Admin"'
            }
        )

    return None

print(
    "AI_API_KEY loaded:",
    bool(API_KEY),
    "length:",
    len(API_KEY) if API_KEY else 0
)

app = Flask(__name__)

CHAT_RATE_LIMIT = 30
CHAT_RATE_WINDOW = 60

chat_requests = {}

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "service": "AI Automation System"
    })


@app.route("/api/v1/health")
def api_v1_health():

    return jsonify({
        "status": "ok",
        "service": "AI Automation System",
        "version": "v1"
    })


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():

    auth_error = require_admin_auth()

    if auth_error:
        return auth_error

    escalations = get_pending_escalations()

    return render_template(
        "dashboard.html",
        escalations=escalations
    )


@app.route("/resolve/<int:escalation_id>", methods=["POST"])
def resolve_case(escalation_id):

    auth_error = require_admin_auth()

    if auth_error:
        return auth_error

    resolve_escalation(escalation_id)

    return redirect("/dashboard")

@app.route("/chat", methods=["POST"])
def customer_chat():

    client_ip = request.remote_addr or "unknown"
    now = time.time()

    recent_requests = chat_requests.get(client_ip, [])

    recent_requests = [
        request_time
        for request_time in recent_requests
        if now - request_time < CHAT_RATE_WINDOW
    ]

    if len(recent_requests) >= CHAT_RATE_LIMIT:

        chat_requests[client_ip] = recent_requests

        return jsonify({
            "error": "Too many requests. Please try again later."
        }), 429

    recent_requests.append(now)
    chat_requests[client_ip] = recent_requests

    try:

        data = request.get_json()

    except Exception:

        return jsonify({
            "error": "Invalid JSON data"
        }), 400


    if not data:

        return jsonify({
            "error": "No JSON data received"
        }), 400


    text = data.get("message")


    if not text or not isinstance(text, str) or not text.strip():

        return jsonify({
            "error": "Message must be a non-empty string"
        }), 400


    if len(text) > 2000:

        return jsonify({
            "error": "Message is too long. Maximum length is 2000 characters."
        }), 400


    try:

        customer_id = data.get("customer_id")

        if (
            not isinstance(customer_id, str)
            or not re.fullmatch(r"WEB-[A-F0-9]{12}", customer_id)
        ):
            customer_id = f"WEB-{uuid.uuid4().hex[:12].upper()}"
        message_id = f"WEBMSG-{uuid.uuid4().hex[:12].upper()}"
        timestamp = datetime.now().isoformat()

        result = run_automation(
            text,
            customer_id,
            message_id,
            timestamp
        )


        if result.get("response"):

            response_text = result["response"]["response"]

        else:

            response_text = (
                "Thank you for your message. "
                "How can we help you?"
            )


        return jsonify({
            "request_id": result["response"]["request_id"],
            "category": result["category"],
            "needs_human": result["needs_human"],
            "response": response_text
        })


    except Exception as error:

        print("Customer chat error:", error)

        return jsonify({
            "response": (
                "Sorry, we're unable to process "
                "your request right now. "
                "Please try again later."
            )
        }), 500


@app.route("/api/v1/message", methods=["POST"])
@app.route("/message", methods=["POST"])
def receive_message():

    try:

        data = request.get_json()

    except Exception:

        return jsonify({
            "error": "Invalid JSON data"
        }), 400


    if not data:

        return jsonify({
            "error": "No JSON data received"
        }), 400


    provided_api_key = request.headers.get("X-API-Key")

    if not API_KEY or provided_api_key != API_KEY:
        return jsonify({
            "error": "Unauthorized"
        }), 401


    text = data.get("message")

    customer_id = data.get("customer_id")
    message_id = data.get("message_id")
    timestamp = data.get("timestamp")

    if (
        not isinstance(customer_id, str)
        or not re.fullmatch(r"WEB-[A-F0-9]{12}", customer_id)
    ):
        return jsonify({
            "error": "Invalid customer_id"
        }), 400


    if (
        not isinstance(message_id, str)
        or not message_id.strip()
    ):
        return jsonify({
            "error": "message_id is required"
        }), 400


    if message_id and is_message_processed(message_id):

        return jsonify({
            "status": "duplicate",
            "message_id": message_id,
            "message": "This message has already been processed."
        }), 200


    if not text or not isinstance(text, str) or not text.strip():

        return jsonify({
            "error": "Message must be a non-empty string"
        }), 400


    if len(text) > 2000:

        return jsonify({
            "error": "Message is too long. Maximum length is 2000 characters."
        }), 400


    print("\nMessage received:")
    print(text)


    try:

        if message_id:

            mark_message_processed(message_id)


        result = run_automation(
            text,
            customer_id,
            message_id,
            timestamp
        )


        if result.get("response"):

            response_text = result["response"]["response"]

        else:

            response_text = (
                "Thank you for your message. "
                "How can we help you?"
            )


        return jsonify({
            "request_id": result["response"]["request_id"],
            "category": result["category"],
            "needs_human": result["needs_human"],
            "response": response_text
        })


    except Exception as error:

        print("Automation error:", error)
    

        return jsonify({
            "response": (
                "Sorry, we're unable to process "
                "your request right now. "
                "Please try again later."
            )
        }), 500


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )

