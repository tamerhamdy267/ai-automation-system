import json
from pathlib import Path


CLIENTS_FILE = Path(__file__).resolve().parent / "clients.json"


def load_clients():

    if not CLIENTS_FILE.exists():
        raise FileNotFoundError(
            f"Client registry not found: {CLIENTS_FILE}"
        )

    with open(CLIENTS_FILE, "r", encoding="utf-8") as file:
        clients = json.load(file)

    if not isinstance(clients, dict):
        raise ValueError("Client registry must be a JSON object.")

    return clients


def get_client_config(client_id):

    clients = load_clients()

    client = clients.get(client_id)

    if not client:
        raise ValueError("Unknown client_id.")

    if not client.get("business_name"):
        raise ValueError("business_name is required.")

    return client
