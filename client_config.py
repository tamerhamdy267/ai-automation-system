import json
from pathlib import Path


CONFIG_FILE = Path(__file__).resolve().parent / "client_config.json"


def load_client_config():

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Client configuration not found: {CONFIG_FILE}"
        )

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = json.load(file)

    if not isinstance(config, dict):
        raise ValueError("Client configuration must be a JSON object.")

    if not config.get("client_id"):
        raise ValueError("client_id is required.")

    if not config.get("business_name"):
        raise ValueError("business_name is required.")

    return config


if __name__ == "__main__":

    config = load_client_config()

    print("Client configuration loaded successfully.")
    print("Client ID:", config["client_id"])
    print("Business:", config["business_name"])