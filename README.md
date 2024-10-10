# Cross-fit - Assistant

## Tech Stacks
* OpenAI as a LLM
* Flask as an API interface (see [Background])(#background) for more info

## Running it
### Running the application

```bash
pipenv run python app.py
```

Testing the application:

```bash
URL=http://localhost:5000

DATA='{"question":"What is the main purpose of performing Glute-Ham Raises in my fitness routine?"}'

curl -X POST \
-H "Content-Type: application/json" \
-d "${DATA}" \
${URL}/ask
```

# How to execute
Using : pipenv 
       python 3.11

Get the follwwing libraries & dependencies installed:

pipenv:

```bash
pip install pipenv
```

dependencies:

```bash
pipenv install
```

Running Jupyter otebbioks for experiments:
```bash
cd notebooks
pipenv run jupyter notebook
```


Running the Flask App:
```bash
pipenv run python app.py
```


## Interface
Uisng Flask APP for serving the application as API endpoints.

# Background

## Flask API with OpenAI as LLM

This project provides a simple API built using Flask to interact with OpenAI's Large Language Model (LLM). The API offers two POST endpoints:

- /ask: Accepts a user question, passes it to an OpenAI-based function for a response, and returns the answer along with a unique conversation ID.
- /feedback: Accepts user feedback on a conversation (positive or negative) for future processing.

## Installation

### Prerequisites
- Python 3.11
- OpenAI API Key (sign up at [OpenAI](https://beta.openai.com/signup/))

### Features
- Flask API: A lightweight Python web framework for building the API.
- OpenAI Integration: Uses OpenAI's language model to process user questions and return responses.
- UUID for Conversations: Automatically generates unique conversation IDs to track interactions.
- Feedback Mechanism: Accepts user feedback for each conversation for future analysis.

### Steps

1. **Clone the Repository**:
   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```

2. **Install Pipenv** (if not already installed):
   ```bash
   pip install pipenv
   ```

3. **Create Pipenv Environment and Install Dependencies**:
   ```bash
   pipenv --python 3.11
   pipenv install openai scikit-learn pandas flask python-dotenv 
   pipenv install --dev 
   ```

4. **Set Environment Variables**:
   Create a `.env` file with the following content:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   ```

5. **Run the Flask App**:
   ```bash
   pipenv run python app.py
   ```

## Usage
- The API will be available at `http://127.0.0.1:5000`.
- Use POST requests to interact with the endpoints.

## Example
```bash
curl -X POST http://localhost:5000/ask \
-H "Content-Type: application/json" \
-d '{"question": "What is the main purpose of performing Glute-Ham Raises in my fitness routine?"}' \
```
and the response is:
```json
{
  "answer": "The main purpose of performing Glute-Ham Raises in your fitness routine is to activate and strengthen the glutes and hamstrings. While the specific exercise isn't mentioned in the context provided, related exercises such as Glute Bridges and Weighted Glute Bridges focus on engaging these muscle groups. Strengthening the glutes and hamstrings is essential for overall lower body strength, stability, and mobility.",
  "conversation_id": "91bfd5d4-9174-464c-9670-a418a7ef6a69",
  "question": "What is the main purpose of performing Glute-Ham Raises in my fitness routine?"
}
```

