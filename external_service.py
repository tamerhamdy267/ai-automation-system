import os
import requests
import time
import logging
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()


API_URL = os.getenv(
    "AI_API_URL",
    "http://127.0.0.1:5000/api/v1/message"
)

API_KEY = os.getenv("AI_API_KEY")

logging.basicConfig(
    filename="external_service.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


messages = [
    {
        "customer_id": "CUST-2001",
        "message_id": "MSG-2001",
        "message": "How much does your service cost?"
    },
    {
        "customer_id": "CUST-2002",
        "message_id": "MSG-2002",
        "message": "I need help with my order"
    },
    {
        "customer_id": "CUST-2003",
        "message_id": "MSG-2003",
        "message": "The API keeps giving me a 500 error"
    },
    {
        "customer_id": "CUST-2004",
        "message_id": "MSG-2004",
        "message": "Can I get a refund after 45 days?"
    }
]


for item in messages:

    payload = {
        "customer_id": item["customer_id"],
        "message_id": item["message_id"],
        "message": item["message"],
        "timestamp": datetime.now().isoformat()
    }

    print("\n" + "=" * 60)

    print("Sending customer message:")
    print(item["message"])

    logging.info(
        "Sending request | customer_id=%s | message_id=%s",
        item["customer_id"],
        item["message_id"]
    )

    response = None

    for attempt in range(1, 4):

        try:

            response = requests.post(
                API_URL,
                headers={
                    "X-API-Key": API_KEY
                },
                json=payload,
                timeout=60
            )

            break

        except requests.RequestException as error:

            logging.error(
                "Request attempt failed | customer_id=%s | attempt=%s | error=%s",
                item["customer_id"],
                attempt,
                error
            )

            print(
                f"Request attempt {attempt} failed: {error}"
            )

            if attempt < 3:

                print("Retrying...")
                time.sleep(2)

            else:

                print("All retry attempts failed.")


    if response is None:

        logging.error(
            "Request failed completely | customer_id=%s | message_id=%s",
            item["customer_id"],
            item["message_id"]
        )

        print("\nRequest failed completely.")
        print("The AI automation server could not be reached.")

        time.sleep(2)
        continue


    print("\nHTTP Status:", response.status_code)


    if response.status_code == 200:

        data = response.json()

        print("Request ID:", data["request_id"])
        print("Category:", data["category"])
        print("Needs human:", data["needs_human"])

        print("\nAI Response:")
        print(data["response"])

        logging.info(
            "Request successful | customer_id=%s | message_id=%s | request_id=%s | status=%s | category=%s | needs_human=%s",
            item["customer_id"],
            item["message_id"],
            data["request_id"],
            response.status_code,
            data["category"],
            data["needs_human"]
        )


    elif response.status_code == 400:

        print("Bad request:")
        print(response.text)

        logging.warning(
            "Bad request | customer_id=%s | message_id=%s | status=%s | response=%s",
            item["customer_id"],
            item["message_id"],
            response.status_code,
            response.text
        )


    elif response.status_code == 404:

        print("API endpoint not found:")
        print(response.text)

        logging.error(
            "API endpoint not found | customer_id=%s | message_id=%s | status=%s",
            item["customer_id"],
            item["message_id"],
            response.status_code
        )


    elif response.status_code >= 500:

        print("Server error:")
        print(response.text)

        logging.error(
            "Server error | customer_id=%s | message_id=%s | status=%s | response=%s",
            item["customer_id"],
            item["message_id"],
            response.status_code,
            response.text
        )


    else:

        print("Unexpected API response:")
        print(response.status_code)
        print(response.text)

        logging.warning(
            "Unexpected response | customer_id=%s | message_id=%s | status=%s",
            item["customer_id"],
            item["message_id"],
            response.status_code
        )


    time.sleep(2)


print("\n" + "=" * 60)
print("External service test completed.")

logging.info("External service test completed.")