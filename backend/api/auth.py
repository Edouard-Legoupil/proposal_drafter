#  Standard Library
import json
import logging
import os
import uuid
from datetime import datetime, timedelta

#  Third-Party Libraries
import httpx
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
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
    jwt,
    ENTRA_TENANT_ID,
    ENTRA_CLIENT_ID,
    ENTRA_CLIENT_SECRET,
)
from backend.models.schemas import UserSettings

# This router handles all authentication-related endpoints, including user
# registration, login, logout, profile management, and password recovery.
router = APIRouter()


@router.get("/sso-status")
async def sso_status():
    """
    Returns the status of SSO.
    """
    return {"enabled": all([ENTRA_TENANT_ID, ENTRA_CLIENT_ID, ENTRA_CLIENT_SECRET])}


@router.get("/sso-login")
async def sso_login():
    """
    Redirects the user to the Microsoft identity platform for authentication.
    """
    if not all([ENTRA_TENANT_ID, ENTRA_CLIENT_ID, ENTRA_CLIENT_SECRET]):
        return JSONResponse(status_code=404, content={"error": "SSO not configured"})
    redirect_uri = os.getenv("VITE_BACKEND_URL", "http://localhost:8000") + "/callback"
    url = (
        f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/oauth2/v2.0/authorize"
        f"?client_id={ENTRA_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&response_mode=query"
        f"&scope=User.Read"
    )
    return RedirectResponse(url=url)


@router.get("/callback")
async def callback(request: Request, code: str):
    """
    Handles the response from the Microsoft identity platform.
    """
    if not all([ENTRA_TENANT_ID, ENTRA_CLIENT_ID, ENTRA_CLIENT_SECRET]):
        return JSONResponse(status_code=404, content={"error": "SSO not configured"})
    redirect_uri = os.getenv("VITE_BACKEND_URL", "http://localhost:8000") + "/callback"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://login.microsoftonline.com/{ENTRA_TENANT_ID}/oauth2/v2.0/token",
                data={
                    "client_id": ENTRA_CLIENT_ID,
                    "scope": "User.Read",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "client_secret": ENTRA_CLIENT_SECRET,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logging.error(f"Failed to get token: {e.response.text}")
            return JSONResponse(
                status_code=400, content={"error": "Failed to get token"}
            )

    access_token = response.json()["access_token"]
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logging.error(f"Failed to get user data: {e.response.text}")
            return JSONResponse(
                status_code=400, content={"error": "Failed to get user data"}
            )

    user_data = response.json()
    email = user_data.get("userPrincipalName") or user_data.get("mail")
    name = user_data.get("displayName")
    if not email:
        return JSONResponse(
            status_code=400, content={"error": "Could not get user email"}
        )

    with get_engine().connect() as connection:
        result = connection.execute(
            text("SELECT id, email, name FROM users WHERE email = :email"),
            {"email": email},
        )
        user = result.fetchone()

    if not user:
        with get_engine().begin() as connection:
            result = connection.execute(
                text("SELECT id FROM teams WHERE name = :name"), {"name": "SSO Users"}
            )
            team = result.fetchone()
            if not team:
                team_id = str(uuid.uuid4())
                connection.execute(
                    text("INSERT INTO teams (id, name) VALUES (:id, :name)"),
                    {"id": team_id, "name": "SSO Users"},
                )
            else:
                team_id = team[0]

            user_id = str(uuid.uuid4())
            connection.execute(
                text(
                    "INSERT INTO users (id, email, name, team_id) VALUES (:id, :email, :name, :team_id)"
                ),
                {"id": user_id, "email": email, "name": name, "team_id": team_id},
            )
    else:
        user_id = user[0]

    token = jwt.encode(
        {"email": email, "exp": datetime.utcnow() + timedelta(minutes=480)},
        SECRET_KEY,
        algorithm="HS256",
    )
    try:
        redis_client.setex(f"user_session:{user_id}", 28800, token)
    except RedisError as redis_error:
        logging.error(
            f"Redis error setting session for user ID {user_id}: {redis_error}"
        )
        pass

    response = RedirectResponse(url="/dashboard")
    cookie_settings = get_cookie_settings(request)
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        path="/",
        max_age=28800,
        **cookie_settings,
    )
    return response


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
    team_id = data.get('team_id')
    security_question = data.get('security_question')
    security_answer = data.get('security_answer')
    settings_data = data.get('settings')

    if not all([name, email, password, security_question, security_answer, team_id, settings_data]):
        return JSONResponse(status_code=400, content={"error": "All fields are required."})

    settings = UserSettings(**settings_data)

    hashed_password = generate_password_hash(password)
    hashed_questions = {security_question: generate_password_hash(security_answer.strip().lower())}
    user_id = str(uuid.uuid4())
    try:
        with get_engine().begin() as connection:
            # Check if a user with the same email already exists.
            result = connection.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": email}
            )
            if result.fetchone():
                return JSONResponse(
                    status_code=400,
                    content={"error": "User with this email already exists."},
                )

            # Insert the new user into the database.
            connection.execute(
                text("""
                    INSERT INTO users (id, email, name, team_id, password, security_questions, geographic_coverage_type, geographic_coverage_region, geographic_coverage_country)
                    VALUES (:id, :email, :name, :team_id, :password, :security_questions, :geographic_coverage_type, :geographic_coverage_region, :geographic_coverage_country)
                """),
                {
                    'id': user_id,
                    'email': email,
                    'name': name,
                    'team_id': team_id,
                    'password': hashed_password,
                    'security_questions': json.dumps(hashed_questions),
                    'geographic_coverage_type': settings.geographic_coverage_type,
                    'geographic_coverage_region': settings.geographic_coverage_region,
                    'geographic_coverage_country': settings.geographic_coverage_country,
                }
            )

            # Insert new roles
            if settings.roles:
                role_insert_query = text("INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)")
                connection.execute(role_insert_query, [{"user_id": user_id, "role_id": role_id} for role_id in settings.roles])

            # Insert new donor groups
            if settings.donor_groups:
                donor_group_insert_query = text("INSERT INTO user_donor_groups (user_id, donor_group) VALUES (:user_id, :donor_group)")
                connection.execute(donor_group_insert_query, [{"user_id": user_id, "donor_group": dg} for dg in settings.donor_groups])

            # Insert new outcomes
            if settings.outcomes:
                outcome_insert_query = text("INSERT INTO user_outcomes (user_id, outcome_id) VALUES (:user_id, :outcome_id)")
                connection.execute(outcome_insert_query, [{"user_id": user_id, "outcome_id": outcome_id} for outcome_id in settings.outcomes])

            # Insert new field contexts
            if settings.field_contexts:
                fc_insert_query = text("INSERT INTO user_field_contexts (user_id, field_context_id) VALUES (:user_id, :fc_id)")
                connection.execute(fc_insert_query, [{"user_id": user_id, "fc_id": fc_id} for fc_id in settings.field_contexts])


        return JSONResponse(status_code=201, content={"message": "Signup successful! Please log in."})
    except Exception as e:
        logging.error(f"[SIGNUP ERROR] {e}")
        return JSONResponse(
            status_code=500, content={"error": "Signup failed. Please try again later."}
        )


@router.post("/login")
async def login(request: Request):
    """
    Handles user login.
    On successful authentication, it creates a JWT and sets it in an HttpOnly cookie.
    """
    try:
        # 1. Parse request body and validate input
        data = await request.json()
        identifier = data.get("identifier") or data.get("email")
        password = data.get("password")

        if not identifier or not password:
            logging.warning(
                "Login attempt failed: Identifier or password not provided."
            )
            return JSONResponse(
                status_code=400,
                content={"error": "Username/email and password are required."},
            )

        try:
            with get_engine().connect() as connection:
                result = connection.execute(
                    text(
                        "SELECT id, email, name, password FROM users WHERE lower(email) = :identifier OR lower(name) = :identifier"
                    ),
                    {"identifier": identifier.strip().lower()},
                )
                user = result.fetchone()
        except SQLAlchemyError as db_error:
            logging.error(
                f"Database error during login for identifier '{identifier}': {db_error}"
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Authentication service is temporarily unavailable. Please try again later."
                },
            )

        if not user:
            logging.warning(f"Login attempt failed for non-existent user: {identifier}")
            return JSONResponse(
                status_code=404, content={"error": "User does not exist!"}
            )

        user_id, email, _, stored_password = user
        if not check_password_hash(stored_password, password):
            logging.warning(
                f"Login attempt failed with invalid password for user ID: {user_id}"
            )
            return JSONResponse(status_code=401, content={"error": "Invalid password!"})

        # 3. Create a JWT token and set Redis session
        token = jwt.encode(
            {"email": email, "exp": datetime.utcnow() + timedelta(minutes=480)},
            SECRET_KEY,
            algorithm="HS256",
        )

        try:
            redis_client.setex(f"user_session:{user_id}", 28800, token)
        except RedisError as redis_error:
            logging.error(
                f"Redis error setting session for user ID {user_id}: {redis_error}"
            )
            pass

        # 4. Set cookie and return success response
        response = JSONResponse(content={"message": "Login successful!"})

        cookie_settings = get_cookie_settings(request)
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            path="/",
            max_age=28800,
            **cookie_settings,
        )
        logging.info(f"User {email} logged in successfully.")
        return response

    except Exception as e:
        # This catch-all is a final safety net.
        # It's better to catch specific exceptions where possible.
        logging.critical(
            f"An unexpected critical error occurred in the login endpoint: {e}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"error": "A server error occurred. Please contact support."},
        )


@router.get("/profile")
async def profile(current_user: dict = Depends(get_current_user)):
    """
    Fetches the profile of the currently authenticated user.
    Relies on the `get_current_user` dependency to ensure the user is logged in.
    """
    try:
        return {
            "message": "Profile fetched successfully",
            "user": {
                "id": current_user["user_id"],
                "name": current_user["name"],
                "email": current_user["email"],
                "roles": current_user.get("roles", []),
                "is_admin": current_user.get("is_admin", False)
            },
        }
    except Exception as e:
        logger.error(f"Error in profile endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch profile")


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
        logging.error(
            f"[LOGOUT ERROR] Failed to remove Redis session for user_id {user_id}: {e}"
        )

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
            {"email": email},
        )
        user = result.fetchone()

    if not user or not user[0]:
        return JSONResponse(
            status_code=404, content={"error": "User or security question not found."}
        )

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
        return JSONResponse(
            status_code=400, content={"error": "All fields are required."}
        )

    with get_engine().connect() as connection:
        result = connection.execute(
            text("SELECT security_questions FROM users WHERE email = :email"),
            {"email": email},
        )
        user = result.fetchone()

    if not user or not user[0]:
        return JSONResponse(
            status_code=404, content={"error": "User or security question not found."}
        )

    stored_questions = json.loads(user[0])
    hashed_answer = stored_questions.get(security_question)

    if not hashed_answer or not check_password_hash(
        hashed_answer, security_answer.strip().lower()
    ):
        return JSONResponse(
            status_code=403, content={"error": "Incorrect security answer."}
        )

    return JSONResponse(
        status_code=200, content={"message": "Security answer verified successfully."}
    )


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
        return JSONResponse(
            status_code=400, content={"error": "All fields are required."}
        )

    try:
        with get_engine().begin() as connection:
            # Re-verify security answer before updating password.
            result = connection.execute(
                text("SELECT security_questions FROM users WHERE email = :email"),
                {"email": email},
            )
            user = result.fetchone()
            if not user or not user[0]:
                raise HTTPException(status_code=404, detail="User not found.")

            stored_questions = json.loads(user[0])
            hashed_answer = stored_questions.get(security_question)

            if not hashed_answer or not check_password_hash(
                hashed_answer, security_answer.strip().lower()
            ):
                raise HTTPException(
                    status_code=403, detail="Incorrect security answer."
                )

            # Update the password.
            hashed_password = generate_password_hash(new_password)
            connection.execute(
                text("UPDATE users SET password = :password WHERE email = :email"),
                {"password": hashed_password, "email": email},
            )
        return JSONResponse(
            status_code=200, content={"message": "Password updated successfully."}
        )
    except Exception as e:
        logging.error(f"[UPDATE PASSWORD ERROR] {e}")
        return JSONResponse(
            status_code=500, content={"error": "Failed to update password."}
        )
