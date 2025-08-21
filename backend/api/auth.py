#  Standard Library
import json
import logging
import uuid
from datetime import datetime, timedelta

#  Third-Party Libraries
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError   

#  Internal Modules
from backend.core.db import get_engine
from backend.core.redis import redis_client
from backend.core.middleware import get_cookie_settings
from backend.core.security import (
    get_current_user,
    generate_password_hash,
    check_password_hash,
    SECRET_KEY,
    jwt
)

# This router handles all authentication-related endpoints, including user
# registration, login, logout, profile management, and password recovery.
router = APIRouter()


@router.post("/signup")
async def signup(request: Request):
    """
    Handles new user registration.
    It hashes the user's password and security answer before storing them.
    """
    data = await request.json()
    name = data.get('username')
    email = data.get('email')
    password = data.get('password')
    security_question = data.get('security_question')
    security_answer = data.get('security_answer')

    if not all([name, email, password, security_question, security_answer]):
        return JSONResponse(status_code=400, content={"error": "All fields are required."})

    hashed_password = generate_password_hash(password)
    hashed_questions = {security_question: generate_password_hash(security_answer.strip().lower())}

    try:
        with get_engine().begin() as connection:
            # Check if a user with the same email already exists.
            result = connection.execute(text("SELECT id FROM users WHERE email = :email"), {'email': email})
            if result.fetchone():
                return JSONResponse(status_code=400, content={"error": "User with this email already exists."})

            # Insert the new user into the database.
            connection.execute(
                text("""
                    INSERT INTO users (id, email, name, password, security_questions)
                    VALUES (:id, :email, :name, :password, :security_questions)
                """),
                {
                    'id': str(uuid.uuid4()),
                    'email': email,
                    'name': name,
                    'password': hashed_password,
                    'security_questions': json.dumps(hashed_questions)
                }
            )
        return JSONResponse(status_code=201, content={"message": "Signup successful! Please log in."})
    except Exception as e:
        logging.error(f"[SIGNUP ERROR] {e}")
        return JSONResponse(status_code=500, content={"error": "Signup failed. Please try again later."})


@router.post("/login")
async def login(request: Request):
    """
    Handles user login.
    On successful authentication, it creates a JWT and sets it in an HttpOnly cookie.
    """
    try:
        # 1. Parse request body and validate input
        data = await request.json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            logging.warning("Login attempt failed: Email or password not provided.")
            return JSONResponse(status_code=400, content={"error": "Email and password are required."})

        # 2. Authenticate user against the database
        try:
            with get_engine().connect() as connection:
                result = connection.execute(
                    text("SELECT id, email, name, password FROM users WHERE email = :email"),
                    {'email': email}
                )
                user = result.fetchone()
        except SQLAlchemyError as db_error:
            # Catch specific database-related errors
            logging.error(f"Database error during login for email '{email}': {db_error}")
            return JSONResponse(status_code=500, content={"error": "Authentication service is temporarily unavailable. Please try again later."})
        
        if not user:
            logging.warning(f"Login attempt failed for non-existent user: {email}")
            return JSONResponse(status_code=404, content={"error": "User does not exist!"})

        user_id, _, _, stored_password = user
        if not check_password_hash(stored_password, password):
            logging.warning(f"Login attempt failed with invalid password for user ID: {user_id}")
            return JSONResponse(status_code=401, content={"error": "Invalid password!"})
        
        # 3. Create a JWT token and set Redis session
        token = jwt.encode(
            {"email": email, "exp": datetime.utcnow() + timedelta(minutes=30)},
            SECRET_KEY,
            algorithm="HS256"
        )
        
        try:
            redis_client.setex(f"user_session:{user_id}", 1800, token)
        except RedisError as redis_error:
            # Catch specific Redis-related errors
            logging.error(f"Redis error setting session for user ID {user_id}: {redis_error}")
            # Do not stop login flow if session storage fails, but log it
            # The user might still be able to access the API if the front-end handles the token correctly
            pass

        # 4. Set cookie and return success response
        response = JSONResponse(content={"message": "Login successful!"})
        
        cookie_settings = get_cookie_settings(request)
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            path="/",
            max_age=1800,
            **cookie_settings
        )
        logging.info(f"User {email} logged in successfully.")
        return response
    
    except Exception as e:
        # This catch-all is a final safety net.
        # It's better to catch specific exceptions where possible.
        logging.critical(f"An unexpected critical error occurred in the login endpoint: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "A server error occurred. Please contact support."})


@router.get("/profile")
async def profile(current_user: dict = Depends(get_current_user)):
    """
    Fetches the profile of the currently authenticated user.
    Relies on the `get_current_user` dependency to ensure the user is logged in.
    """
    return {
        "message": "Profile fetched successfully",
        "user": {
            "name": current_user["name"],
            "email": current_user["email"]
        }
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logs the user out by deleting their session from Redis and clearing the auth cookie.
    """
    user_id = current_user["user_id"]
    try:
        redis_client.delete(f"user_session:{user_id}")
        logging.info(f"[LOGOUT] Removed session for user_id: {user_id}")
    except Exception as e:
        logging.error(f"[LOGOUT ERROR] Failed to remove Redis session for user_id {user_id}: {e}")

    response = JSONResponse(content={"message": "Logout successful!"})
    response.delete_cookie(key="auth_token")
    return response


@router.post("/get-security-question")
async def get_security_question(request: Request):
    """
    Retrieves the security question for a user based on their email.
    This is the first step in the password recovery process.
    """
    data = await request.json()
    email = data.get("email")
    if not email:
        return JSONResponse(status_code=400, content={"error": "Email is required."})

    with get_engine().connect() as connection:
        result = connection.execute(
            text("SELECT security_questions FROM users WHERE email = :email"),
            {"email": email}
        )
        user = result.fetchone()

    if not user or not user[0]:
        return JSONResponse(status_code=404, content={"error": "User or security question not found."})

    stored_questions = json.loads(user[0])
    question = list(stored_questions.keys())[0]
    return JSONResponse(status_code=200, content={"question": question})


@router.post("/verify-security-answer")
async def verify_security_answer(request: Request):
    """
    Verifies a user's answer to their security question.
    """
    data = await request.json()
    email = data.get("email")
    security_question = data.get("security_question")
    security_answer = data.get("security_answer")

    if not all([email, security_question, security_answer]):
        return JSONResponse(status_code=400, content={"error": "All fields are required."})

    with get_engine().connect() as connection:
        result = connection.execute(
            text("SELECT security_questions FROM users WHERE email = :email"),
            {"email": email}
        )
        user = result.fetchone()

    if not user or not user[0]:
        return JSONResponse(status_code=404, content={"error": "User or security question not found."})

    stored_questions = json.loads(user[0])
    hashed_answer = stored_questions.get(security_question)

    if not hashed_answer or not check_password_hash(hashed_answer, security_answer.strip().lower()):
        return JSONResponse(status_code=403, content={"error": "Incorrect security answer."})

    return JSONResponse(status_code=200, content={"message": "Security answer verified successfully."})


@router.post("/update-password")
async def update_password(request: Request):
    """
    Updates a user's password after they have successfully answered their security question.
    """
    data = await request.json()
    email = data.get("email")
    new_password = data.get("new_password")
    # Security answer is re-verified here as a final check.
    security_question = data.get("security_question")
    security_answer = data.get("security_answer")

    if not all([email, new_password, security_question, security_answer]):
        return JSONResponse(status_code=400, content={"error": "All fields are required."})

    try:
        with get_engine().begin() as connection:
            # Re-verify security answer before updating password.
            result = connection.execute(
                text("SELECT security_questions FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()
            if not user or not user[0]:
                raise HTTPException(status_code=404, detail="User not found.")

            stored_questions = json.loads(user[0])
            hashed_answer = stored_questions.get(security_question)

            if not hashed_answer or not check_password_hash(hashed_answer, security_answer.strip().lower()):
                raise HTTPException(status_code=403, detail="Incorrect security answer.")

            # Update the password.
            hashed_password = generate_password_hash(new_password)
            connection.execute(
                text("UPDATE users SET password = :password WHERE email = :email"),
                {"password": hashed_password, "email": email}
            )
        return JSONResponse(status_code=200, content={"message": "Password updated successfully."})
    except Exception as e:
        logging.error(f"[UPDATE PASSWORD ERROR] {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to update password."})
