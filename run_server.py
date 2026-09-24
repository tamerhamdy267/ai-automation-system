import os
from dotenv import load_dotenv
from waitress import serve
from webhook_server import app

load_dotenv()


HOST = os.getenv(
    "SERVER_HOST",
    "127.0.0.1"
)

PORT = int(
    os.getenv(
        "SERVER_PORT",
        "5000"
    )
)


if __name__ == "__main__":

    serve(
        app,
        host=HOST,
        port=PORT
    )