# backend/api/wizzard.py
import json
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field
from typing import Optional, List

from backend.core.db import get_engine
from backend.core.security import get_current_user
from backend.utils.crew_wizzard import WizzardCrew

router = APIRouter()
logger = logging.getLogger(__name__)

class WizzardRequest(BaseModel):
    form_data: dict
    prompt: str

@router.post("/get-insights")
async def get_insights(request: WizzardRequest, current_user: dict = Depends(get_current_user)):
    """
    Analyzes the user's proposal and provides insights and suggestions.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # For simplicity, we'll retrieve all insights from the dummy database.
        # In a real application, you'd filter based on the request's form_data.
        query = text("SELECT * FROM successful_proposals_insights")
        insights = session.execute(query).fetchall()

        if not insights:
            raise HTTPException(status_code=404, detail="No insights found in the knowledge base.")

        # The crew will now receive the user's input and the knowledge base insights
        crew = WizzardCrew().create_crew()
        result = crew.kickoff(inputs={
            'user_proposal': request.dict(),
            'knowledge_base': [dict(row) for row in insights]
        })

        try:
            analysis = json.loads(result) if isinstance(result, str) else result
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Failed to parse analysis. Result: {result}")
            raise HTTPException(status_code=500, detail="Failed to generate analysis.")

        return analysis

    except Exception as e:
        logger.error(f"Error getting insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get insights.")
    finally:
        session.close()
