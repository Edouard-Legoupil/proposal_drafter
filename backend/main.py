#TO RUN THIS CODE - uvicorn main:app --host 172.1.24.95 --port 8501 --reload

#  Standard Library
import json
import os
import re
import uuid
import io
from datetime import datetime
import pprint

#  Third-Party Libraries
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict
import redis
from fastapi.middleware.cors import CORSMiddleware

#  Internal Modules
from crew import ProposalCrew

#  Document Handling (python-docx)
from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

app = FastAPI()

# Allow CORS from specific frontend origin(s)
origins = [
    "http://localhost:8503",   # Frontend URL
    "http://localhost:8502",   # Backend URL
    "http://127.0.0.1:8503",   # Alternative frontend URL
    "*"                        # Allow all origins temporarily for debugging
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



session_data = {}

# Initialize Redis with error handling
try:
    redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    # Test connection
    redis_client.ping()
    print("Successfully connected to Redis")
except redis.ConnectionError:
    print("Warning: Could not connect to Redis. Using in-memory storage as fallback.")
    # Use a simple dict as fallback if Redis is not available
    class DictStorage:
        def __init__(self):
            self.storage = {}
            
        def setex(self, key, ttl, value):
            self.storage[key] = value
            
        def set(self, key, value):
            self.storage[key] = value
            
        def get(self, key):
            return self.storage.get(key)
    
    redis_client = DictStorage()



CONFIG_PATH = "config/templates/iom_proposal_template.json"
SECTIONS = ["Summary", "Rationale", "Project Description", "Partnerships and Coordination", "Monitoring", "Evaluation"]

# Load JSON configuration
with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    proposal_data = json.load(file)

# Store processed sections
generated_sections = {}

class BaseDataRequest(BaseModel):
    form_data: Dict[str, str]  
    project_description: str 

class SectionRequest(BaseModel):
    section: str  

class RegenerateRequest(BaseModel):
    section: str
    concise_input: str

def get_session_id():
    """Generate a unique session ID (UUID) for each user session."""
    return str(uuid.uuid4())  # Later, replace with SSO session ID

@app.post("/api/store_base_data")
async def store_base_data(request: BaseDataRequest):
    session_id = get_session_id()  
    data = {
        "form_data": request.form_data,
        "project_description": request.project_description
    }
    # Store in Redis with a 1-hour expiration (3600 seconds)
    redis_client.setex(session_id, 3600, json.dumps(data))
    
    return {"message": "Base data stored successfully", "session_id": session_id}

@app.get("/api/get_base_data/{session_id}")
async def get_base_data(session_id: str):
    data = redis_client.get(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session data not found")
    
    return json.loads(data)  # Convert JSON string back to dictionary

def regenerate_section_logic(session_id: str, section: str, concise_input: str) -> str:
    """Shared logic for regenerating a section using a custom concise input (from user or evaluator)."""
    session_data_str = redis_client.get(session_id)

    if not session_data_str:
        raise HTTPException(status_code=400, detail="Base data not found. Please store it first.")

    session_data = json.loads(session_data_str)
    form_data = session_data["form_data"]
    project_description = session_data["project_description"]

    section_data = next((s for s in proposal_data["sections"] if s["section_name"] == section), {})
    if not section_data:
        raise HTTPException(status_code=400, detail=f"Invalid section name: {section}")

    instructions = section_data.get("instructions", "")
    word_limit = section_data.get("word_limit", 350)

    proposal_crew = ProposalCrew()
    crew_instance = proposal_crew.regenerate_proposal_crew()

    section_input = {
        "section": section,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": instructions,
        "word_limit": word_limit,
        "concise_input": concise_input
    }

    result = crew_instance.kickoff(inputs=section_input)
    raw_output = result.raw.replace("`", "")
    raw_output = re.sub(r'[\x00-\x1F\x7F]', '', raw_output)  
    print("raw_output==>",raw_output)
    parsed = json.loads(raw_output)

    try:
        parsed = json.loads(raw_output)
        generated_text = parsed.get("generated_content", "").strip()
        evaluation_status = parsed.get("evaluation_status", "")
        feedback = parsed.get("feedback", "")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Invalid JSON response from crew", "details": str(e)}
        )

    if not result:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate content for {section}")

    if "generated_sections" not in session_data:
        session_data["generated_sections"] = {}

    session_data["generated_sections"][section] = generated_text
    redis_client.set(session_id, json.dumps(session_data))

    return generated_text

@app.post("/api/process_section/{session_id}")
async def process_section(session_id: str, request: SectionRequest):
    section = request.section
    session_data_str = redis_client.get(session_id)

    if not session_data_str:
        raise HTTPException(status_code=400, detail="Base data not found. Please store it first.")

    session_data = json.loads(session_data_str)
    form_data = session_data["form_data"]
    project_description = session_data["project_description"]

    section_data = next((s for s in proposal_data["sections"] if s["section_name"] == section), {})
    if not section_data:
        raise HTTPException(status_code=400, detail=f"Invalid section name: {section}")

    instructions = section_data.get("instructions", "")
    word_limit = section_data.get("word_limit", 350)

    proposal_crew = ProposalCrew()
    crew_instance = proposal_crew.generate_proposal_crew()
    print("Loaded Knowledge Sources:", crew_instance.knowledge_sources[0].chunks[:1])
    pprint.pprint(crew_instance.knowledge_sources[0].chunks[:1])

    section_input = {
        "section": section,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": instructions,
        "word_limit": word_limit
    }

    result = crew_instance.kickoff(inputs=section_input)
    raw_output = result.raw.replace("`", "")
    raw_output = re.sub(r'[\x00-\x1F\x7F]', '', raw_output)  
    parsed = json.loads(raw_output)


    try:
        parsed = json.loads(raw_output)
        generated_text = parsed.get("generated_content", "").strip()
        evaluation_status = parsed.get("evaluation_status", "")
        feedback = parsed.get("feedback", "")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Invalid JSON response from crew", "details": str(e)}
        )

    if not result:
        raise HTTPException(status_code=500, detail=f"Failed to generate content for {section}")

    is_flagged = evaluation_status.lower() == "flagged"
    evaluator_feedback = feedback.strip()

    if is_flagged and evaluator_feedback:
        generated_text = regenerate_section_logic(
            session_id=session_id,
            section=section,
            concise_input=evaluator_feedback
        )
        message = f"Initial content flagged. Regenerated using evaluator feedback for {section}"
    else:
        session_data.setdefault("generated_sections", {})[section] = generated_text
        redis_client.set(session_id, json.dumps(session_data))
        message = f"Content generated for {section}"


    return {
        "message": message,
        "generated_text": generated_text
    }


@app.post("/api/regenerate_section/{session_id}")
async def regenerate_section(session_id: str,request: RegenerateRequest):
    """Handles regeneration of a section using a concise input for refinement."""

    section = request.section
    concise_input = request.concise_input

    # ✅ Fetch session data from Redis
    session_data = redis_client.get(session_id)

    if not session_data:
        raise HTTPException(status_code=400, detail="Base data not found. Please store it first.")

    # Convert stored JSON string to dictionary
    session_data = json.loads(session_data)

    # Fetch base context
    form_data = session_data["form_data"]
    project_description = session_data["project_description"]

    # Fetch existing instructions & word limit
    section_data = next((s for s in proposal_data["sections"] if s["section_name"] == section), {})

    if not section_data:
        raise HTTPException(status_code=400, detail=f"Invalid section name: {section}")

    instructions = section_data.get("instructions", "")
    word_limit = section_data.get("word_limit", 350)

    proposal_crew = ProposalCrew()
    crew_instance = proposal_crew.regenerate_proposal_crew()

    section_input = {
        "section": section,
        "form_data": form_data,
        "project_description": project_description,
        "instructions": instructions,
        "word_limit": word_limit,
        "concise_input": concise_input
    }

    result = crew_instance.kickoff(inputs=section_input)
    raw_output = result.raw.replace("`", "")
    raw_output = re.sub(r'[\x00-\x1F\x7F]', '', raw_output)  
    parsed = json.loads(raw_output)

    try:
        parsed = json.loads(raw_output)
        generated_text = parsed.get("generated_content", "").strip()
        evaluation_status = parsed.get("evaluation_status", "")
        feedback = parsed.get("feedback", "")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Invalid JSON response from crew", "details": str(e)}
        )
    

    if not result:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate content for {section}")

    if "generated_sections" not in session_data:
        session_data["generated_sections"] = {}  # Initialize if missing
    session_data["generated_sections"][section] = generated_text
    redis_client.set(session_id, json.dumps(session_data))

    return {
        "message": f"Content regenerated for {section}",
        "generated_text": generated_text
    }


@app.post("/api/generate-document/{session_id}")
async def generate_document(session_id: str):
    """Generates final document in Word format after all sections are processed"""

    session_data = redis_client.get(session_id)
    if not session_data:
        raise HTTPException(status_code=400, detail="Session data not found.")

    session_data = json.loads(session_data)

    generated_sections = session_data.get("generated_sections", {})
    if len(generated_sections) != len(SECTIONS):
        missing_sections = [s for s in SECTIONS if s not in generated_sections]
        raise HTTPException(
            status_code=400,
            detail=f"Not all sections processed yet. Missing: {missing_sections}"
        )

    # ✅ Create a Word document
    doc = Document()
    doc.add_heading("Project Proposal", level=1)

    # ✅ Add form data in table format
    form_data = session_data["form_data"]
    table = doc.add_table(rows=1, cols=2)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Field'
    hdr_cells[1].text = 'Value'

    for key, value in form_data.items():
        row_cells = table.add_row().cells
        row_cells[0].text = key
        row_cells[1].text = value

    doc.add_paragraph("\n")  # Adding a line break

    # ✅ Add section-wise content (with markdown beautification)
    for section, content in generated_sections.items():
        doc.add_heading(section, level=2)

        # Clean markdown syntax
        cleaned_content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)  # Headers
        cleaned_content = re.sub(r'(\*\*|__)(.*?)\1', r'\2', cleaned_content)     # Bold
        cleaned_content = re.sub(r'(\*|_)(.*?)\1', r'\2', cleaned_content)        # Italic
        cleaned_content = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', cleaned_content)    # Inline code

        # Separate bullet points and regular lines
        bullet_lines = []
        normal_lines = []
        for line in cleaned_content.splitlines():
            if re.match(r'^\s*[-*]\s+', line):
                bullet_lines.append(re.sub(r'^\s*[-*]\s+', '', line))
            else:
                normal_lines.append(line)

        if normal_lines:
            paragraph = doc.add_paragraph("\n".join(normal_lines).strip())
            paragraph.paragraph_format.space_after = Pt(12)
            paragraph.paragraph_format.line_spacing = 1.5

        for bullet in bullet_lines:
            doc.add_paragraph(bullet.strip(), style='List Bullet')

    # ✅ Save the document
    folder_name = "proposal-documents"
    os.makedirs(folder_name, exist_ok=True)
    unique_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    file_path = os.path.join(folder_name, f"proposal_document_{unique_id}.docx")

    doc.save(file_path)

    return {
        "message": "Proposal document generated successfully",
        "file_path": file_path
    }


@app.get("/")
def health_check():
    return {"status": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8502)
