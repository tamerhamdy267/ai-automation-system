import ollama


def run(text):

    print("AI workflow started.")

    prompt = f"""
Give a short explanation of this text in 2 sentences:

{text}
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response["message"]["content"]

    print("AI Response:")
    print(result)

    return result
