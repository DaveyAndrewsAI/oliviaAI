from flask import Flask, request, jsonify
from openai import OpenAI
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY")
)

# Connect to Supabase
conn = psycopg2.connect(
    host=os.getenv("SUPABASE_HOST"),
    port=int(os.getenv("SUPABASE_PORT")),
    user=os.getenv("SUPABASE_USER"),
    password=os.getenv("SUPABASE_PASSWORD"),
    database=os.getenv("SUPABASE_DATABASE")
)

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('text')
    
    # Hardcode recipient_id for testing (e.g., "IT_Head")
    recipient_id = "IT_Head"
    
    # Generate embedding with DeepSeek using OpenAI client
    response = client.embeddings.create(input=question, model="text-embedding-ada-002")
    embedding = response.data[0].embedding
    
    # Search Supabase for similar FAQs
    cur = conn.cursor()
    cur.execute(
        "SELECT answer FROM faqs WHERE recipient_id = %s ORDER BY embedding <=> %s LIMIT 1",
        (recipient_id, embedding)
    )
    result = cur.fetchone()
    
    if result:
        return jsonify({"response": f"Olivia: {result[0]}"})
    else:
        # Log unanswered question
        cur.execute(
            "INSERT INTO faqs (recipient_id, question) VALUES (%s, %s)",
            (recipient_id, question)
        )
        conn.commit()
        return jsonify({"response": "Question logged for review."})

if __name__ == '__main__':
    app.run(debug=True)