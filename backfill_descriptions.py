import os
import json
import requests
from dotenv import load_dotenv
from sync_script import (
    load_db, get_jira_headers, get_jira_auth, 
    extract_text_from_adf, create_monday_update,
    JIRA_HOST, JIRA_PROJECT
)

load_dotenv()

def backfill_descriptions():
    db = load_db()
    print("--- Starting Description Backfill ---")
    
    # 1. Fetch all Jira Issues again to extract descriptions
    # (Efficiency: could fetch individually but bulk is easier)
    print("Fetching Jira issues...")
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    payload = {
        "jql": f"project = {JIRA_PROJECT}",
        "fields": ["description", "issuetype", "summary"],
        "maxResults": 500
    }
    
    try:
        resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        issues = resp.json().get("issues", [])
    except Exception as e:
        print(f"Error fetching Jira issues: {e}")
        return

    count = 0
    for issue in issues:
        key = issue['key']
        
        # Check if mapped
        if key in db['jira_to_monday']:
            monday_id = db['jira_to_monday'][key]
            
            # Extract Description
            desc_adf = issue['fields'].get('description')
            desc_text = extract_text_from_adf(desc_adf)
            
            if desc_text and desc_text.strip():
                print(f"[{key}] Found Description. Posting update to Monday Item {monday_id}...")
                create_monday_update(monday_id, f"**Backfilled Description:**\\n{desc_text}")
                count += 1
            else:
                # print(f"[{key}] No description found. Skipping.")
                pass
        else:
            # print(f"[{key}] Not mapped to Monday. Skipping.")
            pass

    print(f"--- Backfill Complete. Updated {count} items. ---")

if __name__ == "__main__":
    backfill_descriptions()
