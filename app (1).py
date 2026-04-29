from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from rag import search, documents, index
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ─────────────────────────────────────────
# SENTIMENT DETECTION
# Simple rule-based sentiment detector
# Judges can ask: "How do you detect sentiment?"
# Answer: We check for positive/negative keywords in the message
# ─────────────────────────────────────────
def detect_sentiment(text):
    text_lower = text.lower()

    negative_words = [
        "angry", "frustrated", "worst", "terrible", "bad", "hate",
        "useless", "pathetic", "disgusting", "horrible", "upset",
        "disappointed", "poor", "wrong", "problem", "issue", "complaint",
        "not working", "failed", "fail", "cheated", "fraud", "stupid"
    ]
    positive_words = [
        "thank", "thanks", "good", "great", "excellent", "helpful",
        "amazing", "awesome", "perfect", "wonderful", "love", "happy",
        "satisfied", "nice", "best", "brilliant"
    ]

    for word in negative_words:
        if word in text_lower:
            return "negative"
    for word in positive_words:
        if word in text_lower:
            return "positive"
    return "neutral"


# ─────────────────────────────────────────
# LANGUAGE DETECTION
# Detects if the student is writing in Hindi
# ─────────────────────────────────────────
def detect_language(text):
    # Check if text contains Hindi/Devanagari Unicode characters
    for char in text:
        if '\u0900' <= char <= '\u097F':
            return "hindi"
    return "english"


# ─────────────────────────────────────────
# MAIN CHAT ENDPOINT
# ─────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_question = data.get("message", "").strip()

    # Conversation history sent from frontend
    # This is a list of previous messages — gives the bot memory
    history = data.get("history", [])

    if not user_question:
        return jsonify({"error": "No message provided"}), 400

    # Step 1: Detect sentiment
    sentiment = detect_sentiment(user_question)

    # Step 2: Detect language
    language = detect_language(user_question)

    # Step 3: RAG — find relevant chunks from knowledge base
    relevant_chunks = search(user_question, documents, index)
    context = "\n\n".join(relevant_chunks)

    # Step 4: Build system prompt based on sentiment + language
    if language == "hindi":
        language_instruction = "The student is writing in Hindi. Please respond in simple Hindi language."
    else:
        language_instruction = "Respond in clear English."

    if sentiment == "negative":
        tone_instruction = "The student seems frustrated or upset. Be extra empathetic, calm, and apologetic in your tone. Start with acknowledging their concern."
    elif sentiment == "positive":
        tone_instruction = "The student seems happy. Match their positive energy and be warm and encouraging."
    else:
        tone_instruction = "Be friendly and helpful."

    system_prompt = f"""You are EduBot, a smart and friendly AI assistant for a college helpdesk.
Your job is to answer student questions clearly and accurately using the college information provided.

Rules:
- Answer ONLY using the provided college information
- If the answer is not in the context, say: "I don't have that information. Please contact the admin office."
- Use bullet points when listing multiple items
- Never make up information
- Always be polite and encouraging
- {tone_instruction}
- {language_instruction}"""

    # Step 5: Build messages list WITH conversation history
    # This gives the bot memory of previous messages in the same session
    messages = [{"role": "system", "content": system_prompt}]

    # Add previous conversation turns (history from frontend)
    for turn in history[-6:]:  # Only last 6 messages to stay within token limit
        messages.append({
            "role": turn["role"],
            "content": turn["content"]
        })

    # Add current question with RAG context
    messages.append({
        "role": "user",
        "content": f"""College Information:
{context}

Student Question: {user_question}"""
    })

    # Step 6: Call Groq LLaMA model
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=600,
        temperature=0.3
    )

    answer = response.choices[0].message.content

    return jsonify({
        "answer": answer,
        "sentiment": sentiment,
        "language": language,
        "status": "success"
    })


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "model": "llama-3.3-70b-versatile",
        "chunks_loaded": len(documents),
        "features": ["RAG", "Sentiment Detection", "Multi-language", "Conversation Memory"]
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)