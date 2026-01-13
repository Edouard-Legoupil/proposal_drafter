import json
import glob

files = glob.glob("/home/edouard/python/proposal_drafter/backend/templates/proposal_template_*.json")
errors = []
for f in files:
    try:
        with open(f, 'r') as fp:
            json.load(fp)
    except Exception as e:
        errors.append(f"{f}: {e}")

if errors:
    print("JSON Errors found:")
    for e in errors:
        print(e)
else:
    print("All JSON files are valid.")
