from database import save_conversation


def log_conversation(result):

    save_conversation(result)

    print("Conversation saved to database.")