import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def inspect_monday_item(item_id):
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            id
            name
            column_values {{
                id
                text
                value
                ... on StatusValue {{
                    index
                    label
                }}
            }}
            subitems {{
                id
                name
                column_values {{
                   id
                   text
                   ... on StatusValue {{
                       index
                       label
                   }}
                }}
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

inspect_monday_item("10848343166")
