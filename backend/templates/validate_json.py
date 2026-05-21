import json
import glob

files = glob.glob("/home/edouard/python/proposal_drafter/backend/templates/proposal_template_*.json")
errors = []
for f in files:
    try:
        with open(f, "r") as fp:
            json.load(fp)
    except Exception as validation_error:
        errors.append(f"{f}: {validation_error}")

if errors:
    print("JSON Errors found:")
    for error_msg in errors:
        print(error_msg)
else:
    print("All JSON files are valid.")
