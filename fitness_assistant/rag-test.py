#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np


# In[3]:


import os
import openai
from getpass import getpass


os.environ['OPENAI_API_KEY'] = getpass()
openai.api_key = os.environ["OPENAI_API_KEY"] 


# In[2]:


# file1 = pd.read_csv('../data/crossfit_exercise_plan_250_unique.csv',sep=";")
file2 = pd.read_csv('../data/crossfit_exercise_plan_batch_1.csv',sep=";")
file3 = pd.read_csv('../data/crossfit_exercise_plan_batch_2.csv',sep=";", header=None)
file3.columns = file2.columns


# In[3]:


# Combine the DataFrames
# combined_df = pd.concat([file1, file2, file3], ignore_index=True)
combined_df = pd.concat([file2, file3], ignore_index=True)


# In[ ]:


get_ipython().system('wget https://raw.githubusercontent.com/alexeygrigorev/minsearch/main/minsearch.py')


# In[4]:


combined_df.columns


# In[5]:


combined_df = combined_df.drop_duplicates(subset=['Exercise Name', 'Crossfit Session Name'])


# In[6]:


combined_df = combined_df.rename(columns={'Crossfit Session Name': 'Session Name'})


# In[7]:


combined_df.count()


# In[8]:


combined_df.columns=combined_df.columns.str.lower().str.replace(' ','_')
combined_df.reset_index(drop=True, inplace=True)

# Replace empty strings with NaN for proper handling
combined_df.replace('', np.nan, inplace=True)

# Remove rows where any column is null
combined_df = combined_df.dropna()

combined_df.insert(0,'id',combined_df.index)

# Resetting the index
combined_df = combined_df.reset_index(drop=True)


# In[9]:


combined_df.isnull().sum()


# In[10]:


combined_df.count()


# In[11]:


combined_df.to_csv('../data/crossfit_exercise_plan_01.csv')


# ## Ingestion

# In[4]:


df = pd.read_csv('../data/crossfit_exercise_plan_01.csv')


# In[5]:


df.columns


# In[6]:


documents = df.to_dict(orient="records")


# In[7]:


documents[0]


# In[18]:


# Function to check for blank or np.nan values in a list of dictionaries
def check_for_blank_nan(input_list):
    if not isinstance(input_list, list):
        raise ValueError("Input must be a list of dictionaries")

    problematic_entries = []

    for entry in input_list:
        if not isinstance(entry, dict):
            raise ValueError("All items in the list must be dictionaries")
        
        keys_with_issues = []
        for key, value in entry.items():
            if value == '' or value is None or (isinstance(value, float) and np.isnan(value)):
                keys_with_issues.append(key)
        
        if keys_with_issues:
            problematic_entries.append({
                'id': entry.get('id'),
                'keys_with_issues': keys_with_issues
            })
    
    return problematic_entries


# In[19]:


# Check the sample dictionary for blank or np.nan values
problematic_keys = check_for_blank_nan(documents)

# Display keys with issues
print("Keys with blank or np.nan values:")
print(problematic_keys)


# In[20]:


import minsearch

index = minsearch.Index(
    text_fields=['exercise_name', 'session_name', 'type_of_activity',
       'type_of_equipment', 'body_part', 'type', 'muscle_groups_activated',
       'instructions'],
    keyword_fields=[]
)


# In[21]:


index.fit(docs=documents)


# ### RAG Flow

# In[22]:


query = "give me leg excercises for hamstrings"


# In[23]:


index.search(query, num_results=10)


# In[24]:


from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[{"role": "user", "content": query}]
)

response.choices[0].message.content


# In[25]:


def search(query):
    boost = {}

    results = index.search(
        query=query,
        filter_dict={},
        boost_dict=boost,
        num_results=10
    )

    return results


# In[26]:


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


# In[27]:


def build_prompt(query, search_results):
    context = ""
    
    for doc in search_results:
        context = context + entry_template.format(**doc) + "\n\n"
    
    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt


# In[28]:


search_results = search(query)
prompt = build_prompt(query, search_results)


# In[29]:


print(prompt)


# In[54]:


def llm(prompt, model='gpt-4o-mini'):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


# In[55]:


def rag(query, model='gpt-4o-mini'):
    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt,model=model)
    return answer


# In[32]:


answer = rag(query, )


# In[33]:


print(answer)


# In[34]:


answer = rag("What is the main purpose of performing Glute-Ham Raises in my fitness routine?")


# In[35]:


print(answer)


# ##  Retrieval Evaluation

# In[36]:


documents[1]


# In[37]:


df_question =pd.read_csv('../data/ground-truth-retrieval.csv')


# In[38]:


df_question.head()


# In[39]:


ground_truth=df_question.to_dict(orient="records")


# In[40]:


def hit_rate(relevance_total):
    cnt = 0

    for line in relevance_total:
        if True in line:
            cnt = cnt + 1

    return cnt / len(relevance_total)


def mrr(relevance_total):
    total_score = 0.0

    for line in relevance_total:
        for rank in range(len(line)):
            if line[rank] == True:
                total_score = total_score + 1 / (rank + 1)

    return total_score / len(relevance_total)


# In[41]:


def minsearch_search(query):
    boost = {}

    results = index.search(
        query=query,
        filter_dict={},
        boost_dict=boost,
        num_results=10
    )

    return results


# In[42]:


def evaluate(ground_truth, search_function):
    relevance_total = []

    for q in tqdm(ground_truth):
        doc_id = q['id']
        results = search_function(q)
        relevance = [d['id'] == doc_id for d in results]
        relevance_total.append(relevance)

    return {
        'hit_rate': hit_rate(relevance_total),
        'mrr': mrr(relevance_total),
    }


# In[43]:


from tqdm.auto import tqdm


# In[33]:


evaluate(ground_truth, lambda q: minsearch_search(q['question']))


# ###  Optimise best hyper parameters for tuning

# In[34]:


from hyperopt import fmin, tpe, hp, STATUS_OK, Trials
from hyperopt.pyll import scope


# In[37]:


df_validation = df_question[:100]
df_test = df_question[100:]


# In[38]:


import random

def simple_optimize(param_ranges, objective_function, n_iterations=10):
    best_params = None
    best_score = float('-inf')  # Assuming we're minimizing. Use float('-inf') if maximizing.

    for _ in range(n_iterations):
        # Generate random parameters
        current_params = {}
        for param, (min_val, max_val) in param_ranges.items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                current_params[param] = random.randint(min_val, max_val)
            else:
                current_params[param] = random.uniform(min_val, max_val)
        
        # Evaluate the objective function
        current_score = objective_function(current_params)
        
        # Update best if current is better
        if current_score > best_score:  # Change to > if maximizing
            best_score = current_score
            best_params = current_params
    
    return best_params, best_score


# In[39]:


gt_val = df_validation.to_dict(orient='records')


# In[40]:


def minsearch_search(query, boost=None):
    if boost is None:
        boost = {}

    results = index.search(
        query=query,
        filter_dict={},
        boost_dict=boost,
        num_results=10
    )

    return results


# In[41]:


param_ranges = {
    'exercise_name': (0.0, 3.0),
    'type_of_activity': (0.0, 3.0),
    'type_of_equipment': (0.0, 3.0),
    'body_part': (0.0, 3.0),
    'type': (0.0, 3.0),
    'muscle_groups_activated': (0.0, 3.0),
    'instructions': (0.0, 3.0),
}

def objective(boost_params):
    def search_function(q):
        return minsearch_search(q['question'], boost_params)

    results = evaluate(gt_val, search_function)
    return results['mrr']


# In[42]:


simple_optimize(param_ranges, objective, n_iterations=20)


# In[43]:


def minsearch_improved(query):
    boost = {'exercise_name': 2.59,
          'type_of_activity': 1.51,
          'type_of_equipment': 0.90,
          'body_part': 2.35,
          'type': 1.81,
          'muscle_groups_activated': 2.46,
          'instructions': 0.04
            }

    results = index.search(
        query=query,
        filter_dict={},
        boost_dict=boost,
        num_results=10
    )

    return results

evaluate(ground_truth, lambda q: minsearch_improved(q['question']))


# ### RAG Evaluation
# either through Cosine Similarity or LLM as a Judge for evaluation.
# 
# Cosine Similarity needs expected questions/answers to validate against., but in our case we son't have expected results to compare with.
# so let's stick to LLM as Judge.

# In[44]:


prompt2_template = """
You are an expert evaluator for a RAG system.
Your task is to analyze the relevance of the generated answer to the given question.
Based on the relevance of the generated answer, you will classify it
as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Question: {question}
Generated Answer: {answer_llm}

Please analyze the content and context of the generated answer in relation to the question
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a brief explanation for your evaluation]"
}}
""".strip()


# In[45]:


len(ground_truth)


# In[56]:


def llm(prompt, model='gpt-4o-mini'):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


# In[57]:


def rag(query, model='gpt-4o-mini'):
    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer = llm(prompt,model=model)
    return answer


# In[58]:


record = ground_truth[0]
question = record['question']
answer_llm = rag(question)


# In[47]:


print(answer_llm)


# In[48]:


prompt = prompt2_template.format(question=question, answer_llm=answer_llm)
print(prompt)


# In[49]:


llm(prompt)


# In[59]:


df_sample = df_question.sample(n=200, random_state=1)


# In[60]:


sample = df_sample.to_dict(orient='records')


# In[61]:


import json


# In[62]:


evaluations = []

for record in tqdm(sample):
    question = record['question']
    answer_llm = rag(question) 

    prompt = prompt2_template.format(
        question=question,
        answer_llm=answer_llm
    )

    evaluation = llm(prompt)
    evaluation = json.loads(evaluation)

    evaluations.append((record, answer_llm, evaluation))


# In[65]:


df_eval = pd.DataFrame(evaluations, columns=['record', 'answer', 'evaluation'])

df_eval['id'] = df_eval.record.apply(lambda d: d['id'])
df_eval['question'] = df_eval.record.apply(lambda d: d['question'])

df_eval['relevance'] = df_eval.evaluation.apply(lambda d: d['Relevance'])
df_eval['explanation'] = df_eval.evaluation.apply(lambda d: d['Explanation'])

del df_eval['record']
del df_eval['evaluation']


# In[66]:


df_eval.relevance.value_counts(normalize=True)


# In[67]:


df_eval.to_csv('../data/rag-eval-gpt-4o-mini.csv', index=False)


# In[68]:


df_eval[df_eval.relevance == 'NON_RELEVANT']


# In[ ]:


evaluations_gpt4o = []

for record in tqdm(sample):
    question = record['question']
    answer_llm = rag(question, model='gpt-4o') 

    prompt = prompt2_template.format(
        question=question,
        answer_llm=answer_llm
    )

    evaluation = llm(prompt)
    evaluation = json.loads(evaluation)
    
    evaluations_gpt4o.append((record, answer_llm, evaluation))


# In[ ]:


df_eval = pd.DataFrame(evaluations_gpt4o, columns=['record', 'answer', 'evaluation'])

df_eval['id'] = df_eval.record.apply(lambda d: d['id'])
df_eval['question'] = df_eval.record.apply(lambda d: d['question'])

df_eval['relevance'] = df_eval.evaluation.apply(lambda d: d['Relevance'])
df_eval['explanation'] = df_eval.evaluation.apply(lambda d: d['Explanation'])

del df_eval['record']
del df_eval['evaluation']


# In[ ]:


df_eval.relevance.value_counts()


# In[ ]:


df_eval.relevance.value_counts(normalize=True)


# In[ ]:


df_eval.to_csv('../data/rag-eval-gpt-4o.csv', index=False)


# In[ ]:




