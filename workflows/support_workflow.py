import json
from datetime import datetime
import uuid

from rag import generate_grounded_response


def clean_response(text):

    text = text.strip()

    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()

    text = text.replace("Dear customer,", "")
    text = text.replace("Dear Customer,", "")
    text = text.replace("Dear [Customer],", "")
    text = text.replace("[Customer],", "")
    text = text.replace("[Your Name]", "")
    text = text.replace("[Your Company]", "")
    text = text.replace("[AI Assistant]", "")

    text = text.replace(
        "Best regards,\n[Your Name]\nCustomer Support Assistant",
        ""
    )

    return text.strip()


def run(customer_message, customer_id=None):

    result = generate_grounded_response(
        customer_message,
        "Support",
        customer_id
    )

    response_text = clean_response(
        result["response"]
    )

    request_id = str(uuid.uuid4())

    timestamp = datetime.now().isoformat(timespec="seconds")

    result_item = {
        "request_id": request_id,
        "timestamp": timestamp,
        "customer_message": customer_message,
        "response": response_text,
        "knowledge_key": result["knowledge_key"],
        "similarity_score": float(result["similarity_score"])
    }

    with open(
        "support_responses.json",
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(result_item) + "\n"
        )

    return result_item
