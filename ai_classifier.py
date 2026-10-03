import json
import re
from datetime import datetime
import uuid
from workflows import sales_workflow
from workflows import support_workflow
from workflows import technical_workflow
from database import save_escalation

from conversation_logger import log_conversation


def classify_text(text):

    text_lower = text.lower()

    sales_keywords = [
        "price",
        "cost",
        "pricing",
        "buy",
        "purchase",
        "quote",
        "plan",
        "discount",
        "negotiate",
        "contract",
        "custom",
        "enterprise"
    ]

    support_keywords = [
        "order",
        "refund",
        "complaint",
        "problem",
        "issue",
        "not working",
        "support",
        "help",
        "cancel",
        "return"
    ]

    technical_keywords = [
        "api",
        "code",
        "python",
        "error",
        "bug",
        "server",
        "database",
        "technical",
        "500",
        "security",
        "data loss",
        "production",
        "hack",
        "breach",
        "unauthorized access"
    ]


    def matches_keyword(keyword):
        if " " in keyword:
            return keyword in text_lower

        return re.search(r"\b" + re.escape(keyword) + r"\b", text_lower) is not None

    if any(matches_keyword(word) for word in support_keywords):
        return "Support"

    if any(matches_keyword(word) for word in sales_keywords):
        return "Sales"

    if any(matches_keyword(word) for word in technical_keywords):
        return "Technical"

    return "Other"

def should_escalate(category, text):
    text_lower = text.lower()

    if category == "Sales":
        return any(word in text_lower for word in [
            "price",
            "cost",
            "pricing",
            "buy",
            "purchase",
            "quote",
            "plan",
            "discount",
            "negotiate",
            "contract",
            "custom",
            "enterprise"
        ])

    if category == "Support":
        if "refund" in text_lower:
            match = re.search(
                r"(\d+)\s*days?",
                text_lower
            )

            if match and int(match.group(1)) > 30:
                return True

            if any(phrase in text_lower for phrase in [
                "after 30 days",
                "over 30 days",
                "more than 30 days"
            ]):
                return True

        if any(word in text_lower for word in [
            "complaint",
            "legal",
            "manager",
            "urgent"
        ]):
            return True

    if category == "Technical":
        return any(word in text_lower for word in [
            "security",
            "data loss",
            "production",
            "database",
            "hack",
            "breach",
            "unauthorized access"
        ])

    return False

def create_escalation(result_item):

    if not result_item["needs_human"]:
        return

    escalation = {
        "customer_id": result_item["customer_id"],
        "message_id": result_item["message_id"],
        "request_id": result_item["response"]["request_id"],
        "timestamp": result_item["response"]["timestamp"],
        "category": result_item["category"],
        "customer_message": result_item["text"],
        "reason": "Requires human review",
        "status": "Pending human review"
    }

    save_escalation(escalation)

    print("Human escalation saved to database.")


def run_automation(
    text,
    customer_id=None,
    message_id=None,
    timestamp=None
):

    category = classify_text(text)

    print("AI Category:", category)

    response = None
    needs_human = False

    if category == "Sales":

        action = "Send to Sales workflow"

        response = sales_workflow.run(text)

        needs_human = should_escalate(category, text)

    elif category == "Support":

        action = "Send to Support workflow"

        response = support_workflow.run(text)

        needs_human = should_escalate(category, text)

    elif category == "Technical":
        text_lower = text.lower()

        security_issue = should_escalate(category, text)

        if security_issue:
            action = "Escalate to human"
            needs_human = True
            response = {
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "customer_message": text,
                "response": (
                    "This message involves a potential security incident "
                    "and has been escalated for human review. "
                    "Please do not share passwords, API keys, access tokens, "
                    "or other credentials."
                ),
                "knowledge_key": "security_incident",
                "similarity_score": 1.0
            }
        else:
            action = "Send to Technical workflow"
            response = technical_workflow.run(text)

    else:

        action = "No action required"

    print("Needs human:", needs_human)

    result_item = {
        "customer_id": customer_id,
        "message_id": message_id,
        "timestamp": timestamp,
        "text": text,
        "category": category,
        "action": action,
        "needs_human": needs_human
    }

    if response:

        result_item["response"] = response

        log_conversation(result_item)

    create_escalation(result_item)

    return result_item


if __name__ == "__main__":

    print("AI Automation System")
    print("Type 'exit' to stop.\n")

    while True:

        text = input("Customer message: ")

        if text.lower() == "exit":
            break

        result = run_automation(text)

        print("\nAI Response:")

        if result.get("response"):
            print(result["response"]["response"])

        else:
            print(
                "Thank you for your message. "
                "How can we help you?"
            )

        print()

