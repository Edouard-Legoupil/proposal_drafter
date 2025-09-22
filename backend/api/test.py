from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from backend.core.db import get_engine
from backend.core.security import get_password_hash
import uuid

router = APIRouter()

@router.post("/test/create-user")
async def create_test_user(email: str, password: str):
    """
    Creates a new user for testing purposes.
    """
    user_id = uuid.uuid4()
    team_id = uuid.uuid4() # Create a dummy team for the user
    hashed_password = get_password_hash(password)

    try:
        with get_engine().begin() as connection:
            # Create a dummy team
            connection.execute(
                text("INSERT INTO teams (id, name) VALUES (:id, :name) ON CONFLICT (id) DO NOTHING"),
                {"id": team_id, "name": "Test Team"}
            )
            # Create the user
            connection.execute(
                text("""
                    INSERT INTO users (id, email, password, name, team_id, created_by, updated_by)
                    VALUES (:id, :email, :password, :name, :team_id, :id, :id)
                """),
                {
                    "id": user_id,
                    "email": email,
                    "password": hashed_password,
                    "name": "Test User",
                    "team_id": team_id,
                }
            )
        return {"message": "Test user created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create test user: {e}")
