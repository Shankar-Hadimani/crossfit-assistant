import pandas as pd
import requests

df = pd.read_csv("./data/ground-truth-retrieval.csv")
question = df.sample(n=1).iloc[0]['question']

print("question: ", question)

url = "http://localhost:5000/ask"


data = {"question": question}

response = requests.post(url, json=data)
# print(response.content)

print("Response status code:", response.status_code)  # Check the status code
print("Response content:", response.content)  # Print the raw content

# Attempt to decode JSON if the response is OK
if response.status_code == 200:
    print(response.json())
else:
    print("Error:", response.status_code)
