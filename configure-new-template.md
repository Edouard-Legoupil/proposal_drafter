# Tutorial to configure a new template


## Back end 

1. Define a new template in `backend/config/templates`

2. Adjust the configuration path in `backend/crew.py`

```
CONFIG_PATH = "config/templates/unhcr_cerf_proposal_template.json"
```

3. Adjust the configuration path in `backend/main.py` l166

```
CONFIG_PATH = "config/templates/unhcr_cerf_proposal_template.json"
SECTIONS = ["Summary", "Rationale", "Project Description", "Partnerships and Coordination", "Monitoring", "Evaluation"]
```

for instance adding more sections - 
SECTIONS = ["Summary", "Rationale", "Project Description", "Partnerships and Coordination", "Monitoring", "Evaluation", "Results Matrix", "Work Plan", "Budget", "Annex 1. Risk Assessment Plan"]

## Front end

1. Adjust the server componnent in `frontend/src/mocks/server.js` l117

2. Adjust the intake form in `frontend/src/screens/chat/chat.jsx` l117

Adjust the predefined list of activities - line 562 & 564



## Adjust Prompting parameters

The formData is collected from end use to be included as part of the context for content generation - 

It is defined within `frontend/src/screens/chat/chat.jsx`