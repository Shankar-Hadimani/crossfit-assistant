from flask import Flask, request, jsonify
from rag import rag
import uuid
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')


app = Flask(__name__)

# In-memory storage for simplicity (replace with DB later)
conversations = {}

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Invoke RAG function
    answer = rag(question)

    # Generate unique conversation ID
    conversation_id = str(uuid.uuid4())

    # Store the conversation result
    conversations[conversation_id] = {"question": question, "answer": answer}

    return jsonify({"conversation_id": conversation_id,
                    "question" :question,
                    "answer": answer})


@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    feedback = data.get('feedback')  # Expected to be +1 or -1

    if not conversation_id or feedback not in [-1, 1]:
        return jsonify({"error": "Invalid conversation ID or feedback"}), 400

    if conversation_id not in conversations:
        return jsonify({"error": "Conversation not found"}), 404

    # Placeholder: Acknowledge feedback (later, write this to a database)
    # conversations[conversation_id]['feedback'] = feedback
    
    result = {"message": "Feedback received", 
              "conversation_id": conversation_id,
              "feedback": feedback}

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
