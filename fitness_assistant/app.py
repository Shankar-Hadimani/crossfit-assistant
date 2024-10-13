from flask import Flask, request, jsonify
from dotenv import load_dotenv, find_dotenv
from db import save_conversation, save_feedback
from rag import rag
import uuid
import os

# Load environment variables from .env file
_ = load_dotenv(find_dotenv())

app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # Invoke RAG function
    answer_data = rag(question)

    # Generate unique conversation ID
    conversation_id = str(uuid.uuid4())

    # Store the conversation result
    save_conversation(conversation_id=conversation_id, 
                      question=question, 
                      answer_data=answer_data)

    return jsonify({"conversation_id": conversation_id,
                    "question" :question,
                    "answer": answer_data['answer']})


@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    feedback = data.get('feedback')  # Expected to be +1 or -1

    if not conversation_id or feedback not in [-1, 1]:
        return jsonify({"error": "Invalid conversation ID or feedback"}), 400


    # Save the feedback
    save_feedback(conversation_id, feedback)
    
    result = {"message": "Feedback received", 
              "conversation_id": conversation_id,
              "feedback": feedback}

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
