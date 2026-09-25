import os

import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)


PROXY_KEY = os.getenv("OLLAMA_PROXY_KEY")


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Ollama AI Proxy"
    })


@app.route("/generate", methods=["POST"])
def generate():

    provided_key = request.headers.get("X-Proxy-Key")

    if not PROXY_KEY or provided_key != PROXY_KEY:
        return jsonify({
            "error": "Unauthorized"
        }), 401


    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No JSON data received"
        }), 400


    prompt = data.get("prompt")

    if not prompt or not isinstance(prompt, str):
        return jsonify({
            "error": "Prompt must be a non-empty string"
        }), 400


    try:

        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        result = response.json()

        return jsonify({
            "response": result["response"]
        })


    except requests.RequestException as error:

        print("Ollama error:", error)

        return jsonify({
            "error": "Ollama is unavailable"
        }), 503


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False
    )