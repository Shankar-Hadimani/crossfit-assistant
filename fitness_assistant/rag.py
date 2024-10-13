from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from time import time 
import ingest
import openai
import json
import os

# Set the API key in the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
index = ingest.load_index()

prompt_template = """
You're a fitness instructor. Answer the QUESTION based on the CONTEXT from the excercise database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

entry_template = """
exercise_name: {exercise_name}
session_name: {session_name}
type_of_activity: {type_of_activity}
type_of_equipment: {type_of_equipment}
body_part: {body_part}
type: {type}
muscle_groups_activated:{muscle_groups_activated}
instructions: {instructions}
""".strip()


evaluation_prompt_template = """
You are an expert evaluator for a RAG system.
Your task is to analyze the relevance of the generated answer to the given question.
Based on the relevance of the generated answer, you will classify it
as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Question: {question}
Generated Answer: {answer}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a brief explanation for your evaluation]"
}}
""".strip()


def search(query):
    boost = {}

    results = index.search(
        query=query,
        filter_dict={},
        boost_dict=boost,
        num_results=10
    )

    return results


def build_prompt(query, search_results):
    context = ""
    
    for doc in search_results:
        context = context + entry_template.format(**doc) + "\n\n"
    
    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt


def llm(prompt, model='gpt-4o-mini'):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    answer = response.choices[0].message.content
    token_stats =  {
        'prompt_tokens':response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
        'total_tokens': response.usage.total_tokens
    }
    
    return answer, token_stats

def evaluate_relevance(question, answer):
    prompt = evaluation_prompt_template.format(question=question, answer=answer)
    evaluation, tokens = llm(prompt, model="gpt-4o-mini")

    try:
        json_eval = json.loads(evaluation)
        return json_eval, tokens
    except json.JSONDecodeError:
        result = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
        return result, tokens

def calculate_openai_cost(model, tokens):
    openai_cost = 0

    if model == "gpt-4o-mini":
        openai_cost = (
            tokens["prompt_tokens"] * 0.00015 + tokens["completion_tokens"] * 0.0006
        ) / 1000
    else:
        print("Model not recognized. OpenAI cost calculation failed.")

    return openai_cost


def rag(query, model='gpt-4o-mini'):
    t_start = time()
    
    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer, token_stats = llm(prompt,model=model)
    relevance, rel_token_stats = evaluate_relevance(query, answer)
    
    t_end = time()
    t_elapsed = t_end - t_start
    prompt_tokens = token_stats['prompt_tokens']
    completion_tokens = token_stats['completion_tokens']
    total_tokens = token_stats['total_tokens']
    
    openai_cost_rag = calculate_openai_cost(model, token_stats)
    openai_cost_eval = calculate_openai_cost(model, rel_token_stats)
    openai_cost = openai_cost_rag + openai_cost_eval
    
    answer_data = {
        "answer":answer,
        "model_used":model,
        "response_time":t_elapsed,
        "relevance":relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation":relevance.get(
            "Explanation", "Failed to parse evaluation"
        ),
        "prompt_tokens":prompt_tokens,
        "completion_tokens":completion_tokens,
        "total_tokens":total_tokens,
        "eval_prompt_tokens":rel_token_stats["prompt_tokens"],
        "eval_completion_tokens":rel_token_stats["completion_tokens"],
        "eval_total_tokens":rel_token_stats["total_tokens"],
        "openai_cost":openai_cost
    }
    
    return answer_data


