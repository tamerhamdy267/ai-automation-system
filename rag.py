import json
import os
import re
import requests

from dotenv import load_dotenv

from database import (
    get_conversation_history,
    save_customer_memory,
    get_customer_memory
)


load_dotenv()


OLLAMA_PROXY_URL = os.getenv(
    "OLLAMA_PROXY_URL",
    "http://127.0.0.1:8000/generate"
)

OLLAMA_PROXY_KEY = os.getenv(
    "OLLAMA_PROXY_KEY",
    ""
).strip()


# =============================================================
# COMPANY KNOWLEDGE
# =============================================================

with open(
    "knowledge.json",
    "r",
    encoding="utf-8"
) as file:

    knowledge = json.load(file)


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "can", "could",
    "do", "does", "for", "from", "get", "has", "have", "how",
    "i", "if", "in", "is", "it", "me", "my", "of", "on", "or",
    "our", "please", "the", "this", "to", "was", "we", "what",
    "when", "where", "which", "with", "you", "your"
}


KEYWORDS = {

    "pricing": {
        "price", "prices", "pricing", "cost", "costs",
        "buy", "purchase", "quote", "quotes", "discount",
        "plan", "plans", "custom"
    },

    "support_hours": {
        "hours", "hour", "open", "closed", "available",
        "availability", "monday", "friday"
    },

    "refund_policy": {
        "refund", "refunds", "money", "purchase", "return",
        "days", "30"
    },

    "enterprise_plan": {
        "enterprise", "business", "company", "companies"
    },

    "api_support": {
        "api", "endpoint", "error", "errors", "500",
        "technical", "code", "server", "bug"
    },

    "order_support": {
        "order", "orders", "order_number", "delivery",
        "shipping", "shipment"
    },

    "security_incident": {
        "security", "breach", "production",
        "database", "data loss", "unauthorized access",
        "hack"
    }
}


def tokenize(text):

    words = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        text.lower()
    )

    return {
        word
        for word in words
        if word not in STOP_WORDS
    }


def retrieve_knowledge(question):

    question_words = tokenize(question)

    best_key = None
    best_score = 0

    for key, value in knowledge.items():

        knowledge_text = (
            f"{key} {value}"
        ).lower()

        knowledge_words = tokenize(
            knowledge_text
        )

        common_words = question_words.intersection(
            knowledge_words
        )

        score = len(common_words)

        topic_keywords = KEYWORDS.get(
            key,
            set()
        )

        keyword_matches = question_words.intersection(
            topic_keywords
        )

        score += len(keyword_matches) * 3

        if score > best_score:

            best_score = score
            best_key = key

    if best_key is None:

        best_key = "support_hours"
        best_score = 0

    return {
        "key": best_key,
        "content": knowledge[best_key],
        "score": best_score
    }


# =============================================================
# REFUND
# =============================================================

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


# =============================================================
# CUSTOMER MEMORY
# =============================================================

def detect_customer_memory(text):

    text_lower = text.lower().strip()

    # ---------------------------------------------------------
    # Do not extract memories from questions.
    # ---------------------------------------------------------

    if text_lower.endswith("?"):
        return None

    question_starts = (
        "what ",
        "why ",
        "when ",
        "where ",
        "who ",
        "which ",
        "how ",
        "do ",
        "does ",
        "did ",
        "can ",
        "could ",
        "would ",
        "should ",
        "is ",
        "are "
    )

    if text_lower.startswith(question_starts):
        return None

    # ---------------------------------------------------------
    # NAME
    # ---------------------------------------------------------

    match = re.match(
        r"^my name is\s+(.+?)(?:\s+and\b|\s+but\b|\s+because\b|[.!?]|$)",
        text,
        re.IGNORECASE
    )

    if match:

        value = match.group(1).strip()

        if value:

            return {
                "key": "Name",
                "value": value
            }

    # ---------------------------------------------------------
    # LOCATION
    # ---------------------------------------------------------

    match = re.match(
        r"^i live in\s+(.+?)\.?$",
        text,
        re.IGNORECASE
    )

    if match:

        value = match.group(1).strip()

        if value:

            return {
                "key": "Current Location",
                "value": value
            }

    # ---------------------------------------------------------
    # FAVOURITE FOOD
    # ---------------------------------------------------------

    match = re.match(
        r"^my favourite food is\s+(.+?)\.?$",
        text,
        re.IGNORECASE
    )

    if not match:

        match = re.match(
            r"^my favorite food is\s+(.+?)\.?$",
            text,
            re.IGNORECASE
        )

    if match:

        value = match.group(1).strip()

        if value:

            return {
                "key": "Favourite Food",
                "value": value
            }

    # ---------------------------------------------------------
    # FAVOURITE COLOR
    # ---------------------------------------------------------

    match = re.match(
        r"^my favourite color is\s+(.+?)\.?$",
        text,
        re.IGNORECASE
    )

    if not match:

        match = re.match(
            r"^my favorite color is\s+(.+?)\.?$",
            text,
            re.IGNORECASE
        )

    if match:

        value = match.group(1).strip()

        if value:

            return {
                "key": "Favourite Color",
                "value": value
            }

    # ---------------------------------------------------------
    # JOB
    # ---------------------------------------------------------

    match = re.match(
        r"^i am a\s+(.+?)\.?$",
        text,
        re.IGNORECASE
    )

    if match:

        value = match.group(1).strip()

        if value:

            return {
                "key": "Job",
                "value": value
            }

    # ---------------------------------------------------------
    # CAREER GOAL
    # ---------------------------------------------------------

    match = re.match(
        r"^my career goal is\s+(.+?)\.?$",
        text,
        re.IGNORECASE
    )

    if match:

        value = match.group(1).strip()

        if value:

            return {
                "key": "Career Goal",
                "value": value
            }

    # ---------------------------------------------------------
    # GENERAL "I want to..."
    # ---------------------------------------------------------

    match = re.match(
        r"^i want to\s+(.+?)\.?$",
        text,
        re.IGNORECASE
    )

    if match:

        value = match.group(1).strip()

        if value:

            return {
                "key": "Goal",
                "value": value
            }

    return None


def save_detected_customer_memory(
    customer_id,
    question
):

    if not customer_id:
        return None

    memory = detect_customer_memory(question)

    if not memory:
        return None

    save_customer_memory(
        customer_id,
        memory["key"],
        memory["value"]
    )

    print(
        f"Customer memory saved: "
        f"{memory['key']} = {memory['value']} "
        f"for {customer_id}"
    )

    return memory


# =============================================================
# MEMORY QUESTION DETECTION
# =============================================================

def is_customer_memory_question(question):

    question_lower = (
        question.lower()
        .strip()
    )

    if "my name" in question_lower:
        return True

    memory_phrases = [

        "what did i tell you",

        "what did i tell you about",

        "what i told you",

        "what was my name",

        "what is my name",

        "do you remember my name",

        "do you remember what i",

        "did i tell you",

        "did i mention",

        "what did i say",

        "what i said earlier",

        "what i said before",

        "what i mentioned earlier",

        "what i mentioned before",

        "what i previously told you",

        "what i told you earlier",

        "what i told you before",

        "what did i give you",

        "what name did i give you",

        "remind me what name",

        "remind me of my name"

    ]

    return any(
        phrase in question_lower
        for phrase in memory_phrases
    )


def answer_customer_memory_question(
    question,
    customer_id
):

    memories = get_customer_memory(
        customer_id
    )

    if not memories:

        return (
            "I do not have that information."
        )

    question_lower = question.lower()

    # ---------------------------------------------------------
    # Direct NAME lookup
    # ---------------------------------------------------------

    if (
        "name" in question_lower
        or "what was my name" in question_lower
        or "what is my name" in question_lower
    ):

        for key, value, created_at, updated_at in memories:

            if key.lower() == "name":

                return (
                    f"Your name is {value}."
                )

        return (
            "I do not have that information."
        )

    # ---------------------------------------------------------
    # Other explicit memory categories
    # ---------------------------------------------------------

    category_words = {

        "location": "Current Location",

        "live": "Current Location",

        "favourite food": "Favourite Food",

        "favorite food": "Favourite Food",

        "favourite color": "Favourite Color",

        "favorite color": "Favourite Color",

        "job": "Job",

        "career": "Career Goal",

        "career goal": "Career Goal",

        "goal": "Goal"
    }

    for phrase, memory_key in category_words.items():

        if phrase in question_lower:

            for key, value, created_at, updated_at in memories:

                if key.lower() == memory_key.lower():

                    return (
                        f"Your {key.lower()} is {value}."
                    )

            return (
                "I do not have that information."
            )

    # ---------------------------------------------------------
    # General memory question.
    #
    # Use the stored customer memories directly rather than
    # asking the LLM to rediscover them.
    # ---------------------------------------------------------

    memory_lines = []

    for key, value, created_at, updated_at in memories:

        memory_lines.append(
            f"{key}: {value}"
        )

    memory_context = "\n".join(
        memory_lines
    )

    prompt = f"""
You are a customer memory assistant.

CUSTOMER MEMORY:

{memory_context}

CURRENT QUESTION:

{question}

Answer using ONLY the customer memory above.

If the answer is present, answer directly.

If the answer is not present, say exactly:

I do not have that information.

Do not invent information.
Do not use company information.
Do not use information about another customer.
Return only the customer-facing answer.
"""

    response = requests.post(

        OLLAMA_PROXY_URL,

        headers={
            "X-Proxy-Key": OLLAMA_PROXY_KEY
        },

        json={
            "prompt": prompt
        },

        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    return result["response"].strip()


# =============================================================
# MAIN RAG RESPONSE
# =============================================================

def generate_grounded_response(
    question,
    category,
    customer_id=None
):

    # ---------------------------------------------------------
    # Save explicit personal information FIRST.
    #
    # This happens before generating the response so that the
    # customer's memory is immediately persistent.
    # ---------------------------------------------------------

    save_detected_customer_memory(
        customer_id,
        question
    )

    # ---------------------------------------------------------
    # Memory question
    # ---------------------------------------------------------

    if is_customer_memory_question(question):

        answer = answer_customer_memory_question(
            question,
            customer_id
        )

        return {

            "response": answer,

            "knowledge_key": "customer_memory",

            "similarity_score": 1.0
        }

    # ---------------------------------------------------------
    # Deterministic refund handling
    # ---------------------------------------------------------

    refund_response = deterministic_refund_response(
        question
    )

    if refund_response:

        return {

            "response": refund_response,

            "knowledge_key": "refund_policy",

            "similarity_score": 1.0
        }

    # ---------------------------------------------------------
    # Conversation history
    #
    # Used only as context for normal customer-support answers.
    # ---------------------------------------------------------

    conversation_history = get_conversation_history(
        customer_id,
        limit=5
    )

    history_context = ""

    if conversation_history:

        history_lines = []

        for row in reversed(
            conversation_history
        ):

            history_lines.append(

                f"Customer: {row[3]}\n"
                f"Assistant: {row[5]}"

            )

        history_context = "\n\n".join(
            history_lines
        )

    # ---------------------------------------------------------
    # Retrieve company knowledge
    # ---------------------------------------------------------

    retrieved = retrieve_knowledge(
        question
    )

    company_information = retrieved[
        "content"
    ]

    # ---------------------------------------------------------
    # Category-specific instructions
    # ---------------------------------------------------------

    if retrieved["key"] == "pricing":

        instruction = """
The customer is asking about pricing.

The company does NOT provide a specific price in the information.

Tell the customer that pricing depends on their specific
requirements and that the sales team can provide a detailed quote.

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
- Do NOT say approval is required.
- Do NOT invent a timeline.

If the customer's request is within 30 days:

- State that the request is within the stated 30-day period.
- Do NOT guarantee approval or issuance.
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

The customer may provide their order number and relevant
non-sensitive details.

Do not invent order status, delivery dates, refund decisions,
prices, or other information that is not provided.

Never request passwords, API keys, access tokens, or credentials.
"""

    else:

        instruction = """
Answer using only the company information provided.
"""

    # ---------------------------------------------------------
    # Normal company RAG prompt
    # ---------------------------------------------------------

    prompt = f"""
You are a customer support AI assistant.

COMPANY INFORMATION:

{company_information}


CUSTOMER CONVERSATION CONTEXT:

{
    history_context
    if history_context
    else "No previous conversation history is available."
}


CURRENT CUSTOMER QUESTION:

{question}


RULES:

1. Use the company information for company facts,
   policies, procedures, prices and limits.

2. Customer-specific information may only come from the
   current customer conversation or this customer's stored memory.

3. Never invent customer information.

4. Never invent company information.

5. Never use another customer's information.

6. Never request passwords, API keys, access tokens,
   or credentials.

7. Be concise, clear, friendly and professional.

8. Return ONLY the customer-facing answer.

9. Do not use placeholders.

10. Do not include a signature.


SPECIFIC TASK:

{instruction}
"""

    response = requests.post(

        OLLAMA_PROXY_URL,

        headers={
            "X-Proxy-Key": OLLAMA_PROXY_KEY
        },

        json={
            "prompt": prompt
        },

        timeout=120
    )

    response.raise_for_status()

    result = response.json()

    return {

        "response": result[
            "response"
        ].strip(),

        "knowledge_key": retrieved[
            "key"
        ],

        "similarity_score": retrieved[
            "score"
        ]
    }