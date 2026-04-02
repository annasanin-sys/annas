import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def inspect_board():
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        boards (ids: {MONDAY_BOARD_ID}) {{
            name
            columns {{
                id
                title
                type
                settings_str
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        
        boards = data.get("data", {}).get("boards", [])
        if not boards:
            print("Board not found.")
            return

        board = boards[0]
        print(f"Board: {board['name']}")
        print("-" * 30)
        
        for col in board['columns']:
            print(f"Column: {col['title']} (ID: {col['id']}, Type: {col['type']})")
            if col['type'] in ["color", "status"]: # Check for both
                try:
                    settings = json.loads(col['settings_str'])
                    print("  Labels:")
                    labels = settings.get("labels", {})
                    for key, label in labels.items():
                        print(f"    - {key}: {label}")
                    
                    # Also checking for label colors just in case
                    # labels_colors = settings.get("labels_colors", {})
                    
                except Exception as e:
                    print(f"  Error parsing settings: {e}")
            print("-" * 15)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_board()
