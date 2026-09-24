from database import get_pending_escalations
from database import resolve_escalation


def show_pending_escalations():

    rows = get_pending_escalations()

    if not rows:
        print("No pending escalations.")
        return

    print("\nPending Human Reviews:\n")

    for row in rows:

        escalation_id = row[0]
        customer_id = row[1]
        message_id = row[2]
        category = row[3]
        customer_message = row[4]
        reason = row[5]
        status = row[6]

        print("ID:", escalation_id)
        print("Customer:", customer_id)
        print("Message ID:", message_id)
        print("Category:", category)
        print("Message:", customer_message)
        print("Reason:", reason)
        print("Status:", status)
        print("-" * 50)


def resolve_case():

    rows = get_pending_escalations()

    if not rows:
        print("No pending escalations.")
        return

    show_pending_escalations()

    escalation_id = input(
        "\nEnter the escalation ID to resolve: "
    )

    try:

        escalation_id = int(escalation_id)

    except ValueError:

        print("Invalid escalation ID.")
        return

    resolve_escalation(escalation_id)

    print("\nEscalation resolved successfully.")


if __name__ == "__main__":

    print("Human Review System")

    while True:

        print("\n1. View pending escalations")
        print("2. Resolve escalation")
        print("3. Exit")

        choice = input("\nChoose an option: ")

        if choice == "1":

            show_pending_escalations()

        elif choice == "2":

            resolve_case()

        elif choice == "3":

            print("Exiting human review system.")
            break

        else:

            print("Invalid option.")