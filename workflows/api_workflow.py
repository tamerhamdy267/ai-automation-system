import requests


def run(text):

    print("API workflow started.")

    url = "https://jsonplaceholder.typicode.com/posts"

    data = {
        "title": "AI classified text",
        "body": text,
        "userId": 1
    }

    response = requests.post(url, json=data)

    response.raise_for_status()

    result = response.json()

    print("API Status:", response.status_code)
    print("API ID:", result["id"])

    return result
