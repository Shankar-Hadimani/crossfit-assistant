import pandas as pd
import numpy as np
import os
import openai
from getpass import getpass
import minsearch


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


def load_index(path='../data/crossfit_exercise_plan_01.csv'):
     
    df = pd.read_csv(path)
    documents = df.to_dict(orient="records")
    
    index = minsearch.Index(
        text_fields=[
            'exercise_name', 
            'session_name', 
            'type_of_activity',
            'type_of_equipment', 
            'body_part', 
            'type', 
            'muscle_groups_activated',
            'instructions'
        ],
        keyword_fields=[]
    )

    index.fit(docs=documents)
    
    return index