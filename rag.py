import json
import requests
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


# Load company knowledge
with open("knowledge.json", "r", encoding="utf-8") as file:
    knowledge = json.load(file)


def retrieve_knowledge(question):

    question_embedding = model.encode([question])

    best_key = None
    best_score = -1

    for key, value in knowledge.items():

        knowledge_embedding = model.encode([value])

        score = cosine_similarity(
            question_embedding,
            knowledge_embedding
        )[0][0]

        if score > best_score:
            best_score = score
            best_key = key

    return {
        "key": best_key,
        "content": knowledge[best_key],
        "score": best_score
    }

def deterministic_refund_response(question):

        question_lower = question.lower()

        match = re.search(
            r"(\d+)\s*days?",
            question_lower
        )

        if not match:
            return None

        days = int(match.group(1))

        if days > 30:

            return (
                "Your refund request is outside the stated "
                "30-day refund period and requires human review."
            )

        return (
            "Your refund request is within the stated "
            "30-day refund period."
        )

def generate_grounded_response(question, category):

    refund_response = deterministic_refund_response(question)

    if refund_response:

        return {
            "response": refund_response,
            "knowledge_key": "refund_policy",
            "similarity_score": 1.0
        }

    
    retrieved = retrieve_knowledge(question)

    company_information = retrieved["content"]

    if retrieved["key"] == "pricing":

        instruction = """
The customer is asking about pricing.

The company does NOT provide a specific price in the information.
Tell the customer that pricing depends on their specific
requirements and that the sales team can provide a detailed quote.

Do NOT say that there is not enough information.
Do NOT invent a price.
"""

    elif retrieved["key"] == "refund_policy":

        instruction = """
    The customer is asking about a refund.

    The company policy is exactly:
    Customers can request a refund within 30 days of purchase.
    Refund requests after 30 days require human review.

    If the customer's request is after 30 days:
    - State that the request is outside the 30-day period.
    - State that it requires human review.
    - Do NOT say the refund is denied.
    - Do NOT say the refund cannot be processed.
    - Do NOT say approval is required.
    - Do NOT invent a timeline.
    - Do NOT invent next steps.

    If the customer's request is within 30 days:
    - State that the request is within the stated 30-day period.
    - Do NOT guarantee that the refund will be approved or issued.

    Use only the policy above.
    """

    elif retrieved["key"] == "support_hours":

        instruction = """
The customer is asking about support hours.

State the support hours exactly as provided.
"""

    elif retrieved["key"] == "enterprise_plan":

        instruction = """
The customer is asking about the enterprise plan.

Explain that enterprise customers should contact the sales team
to discuss their specific requirements.
Do not invent enterprise features or pricing.
"""

    elif retrieved["key"] == "api_support":

        instruction = """
    The customer has an API-related issue.

    Explain that they can provide the API endpoint, error message,
    and relevant non-sensitive troubleshooting details.

    Never request passwords, API keys, access tokens, or credentials.
    """

    elif retrieved["key"] == "order_support":

        instruction = """
    The customer is asking about an order.

    Explain that customer support can assist with order-related questions.
    The customer may provide their order number and relevant non-sensitive
    details.

    Do not invent order status, delivery dates, refund decisions, prices,
    or other information that is not provided.

    Never request passwords, API keys, access tokens, or credentials.
    """

    else:

        instruction = """
Answer using only the company information provided.
"""


    prompt = f"""
You are a customer support AI assistant.

Customer category:
{category}

Company information:
{company_information}

Customer question:
{question}

Specific instruction:
{instruction}

General rules:
- The company information is the only source of truth.
- Use ONLY facts explicitly stated in the company information.
- Do not invent or assume any additional facts.
- Do not invent prices, discounts, guarantees, features,
  policies, teams, procedures, timelines, contact methods,
  promises, or outcomes.
- Do not add deadlines or response times unless explicitly stated.
- Do not say that someone "will contact" the customer unless
  the company information explicitly says so.
- Do not change numbers, dates, limits, or conditions.
- If the company information does not contain a requested detail,
  say that the available company information does not specify it.
- Never request passwords, API keys, access tokens, or credentials.
- Be concise, clear, friendly, and professional.
- Return ONLY the customer-facing response.
- Do not use placeholders.
- Do not include a signature.
"""

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
    )

    response.raise_for_status()

    return {
        "response": response.json()["response"].strip(),
        "knowledge_key": retrieved["key"],
        "similarity_score": retrieved["score"]
    }