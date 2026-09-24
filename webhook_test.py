import os
import requests
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()


WEBHOOK_URL = os.getenv(
    "AI_API_URL",
    "http://127.0.0.1:5000/api/v1/message"
)

API_KEY = os.getenv("AI_API_KEY")


event = {
    "customer_id": "WEBHOOK-CUST-001",
    "message_id": "WEBHOOK-MSG-001",
    "message": "Can I get a refund after 20 days?",
    "timestamp": datetime.now().isoformat()
}


print("Sending webhook event...")
print("Webhook URL:", WEBHOOK_URL)
print("Customer:", event["customer_id"])
print("Message:", event["message"])


try:

    response = requests.post(
        WEBHOOK_URL,
        headers={
            "X-API-Key": API_KEY
        },
        json=event,
        timeout=60
    )
      

    print("\nHTTP Status:", response.status_code)

    data = response.json()

    if response.status_code == 200:

        if data.get("status") == "duplicate":

            print("Status:", data["status"])
            print("Message ID:", data["message_id"])
            print("Message:", data["message"])

        else:

            print("Request ID:", data["request_id"])
            print("Category:", data["category"])
            print("Needs human:", data["needs_human"])

            print("\nAI Response:")
            print(data["response"])

    else:

        print("\nWebhook failed:")
        print(data)


except requests.RequestException as error:

    print("\nConnection error:")
    print(error)