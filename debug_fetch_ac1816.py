import os
import requests
from dotenv import load_dotenv
from sync_script import fetch_jira_issues, JIRA_PROJECT

load_dotenv()

print(f"Project: {JIRA_PROJECT}")

# 1. Run the actual fetch function
parents, subtasks = fetch_jira_issues()
print(f"Fetched {len(parents)} parents and {len(subtasks)} subtasks.")

found = False
for p in parents:
    if p['key'] == 'AC-1816':
        print("FOUND AC-1816 in Parents!")
        print(f"Status: {p['fields']['status']['name']}")
        found = True
        break

if not found:
    for s in subtasks:
        if s['key'] == 'AC-1816':
            print("FOUND AC-1816 in Subtasks!")
            found = True
            break

if not found:
    print("AC-1816 NOT FOUND in fetch results. Checking JQL limit...")
