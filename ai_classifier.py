import json
import re

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
        "500"
    ]

    if any(word in text_lower for word in sales_keywords):
        return "Sales"

    if any(word in text_lower for word in support_keywords):
        return "Support"

    if any(word in text_lower for word in technical_keywords):
        return "Technical"

    return "Other"


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

        text_lower = text.lower()

        if any(word in text_lower for word in [
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
        ]):
            needs_human = True

    elif category == "Support":

        action = "Send to Support workflow"

        response = support_workflow.run(text)

        text_lower = text.lower()


        if "refund" in text_lower:

            match = re.search(
                r"(\d+)\s*days?",
                text_lower
            )

            if match:

                days = int(match.group(1))

                if days > 30:
                    needs_human = True

            if any(phrase in text_lower for phrase in [
                "after 30 days",
                "over 30 days",
                "more than 30 days"
            ]):
                needs_human = True

        if any(word in text_lower for word in [
            "complaint",
            "legal",
            "manager",
            "urgent"
        ]):
            needs_human = True

    elif category == "Technical":

        action = "Send to Technical workflow"

        response = technical_workflow.run(text)

        text_lower = text.lower()

        if any(word in text_lower for word in [
            "security",
            "data loss",
            "production",
            "database",
            "hack",
            "breach"
        ]):
            needs_human = True

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

