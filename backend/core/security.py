#  Standard Library
from datetime import datetime, timedelta

#  Third-Party Libraries
import jwt
from fastapi import Request, HTTPException
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash

#  Internal Modules
from backend.core.config import SECRET_KEY
from backend.core.db import engine

# This module centralizes security-related functions, such as authentication,
# token handling, and password management.


def get_current_user(request: Request) -> dict:
    """
    Dependency function to retrieve and validate a user from a JWT token.

    This function is intended to be used with FastAPI's dependency injection system.
    It performs the following steps:
    1. Extracts the 'auth_token' from the request cookies.
    2. Decodes the JWT to get the user's email.
    3. Queries the database to find the corresponding user.
    4. Returns the user's information or raises an HTTPException on failure.

    Args:
        request: The incoming FastAPI request object.

    Returns:
        A dictionary containing the user's ID, name, and email.

    Raises:
        HTTPException: If the token is missing, invalid, expired, or the user is not found.
    """
    token = request.cookies.get("auth_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token missing.")

    try:
        # Decode the JWT token using the secret key.
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        # Fetch the user from the database.
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT id, name, email FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Return user data as a dictionary.
        return {
            "user_id": str(user[0]),
            "name": user[1],
            "email": user[2]
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
    except Exception as e:
        # Generic error for other potential issues.
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


# Exposing password hashing functions for use in other parts of the application.
# This keeps security-related utilities grouped together.
__all__ = [
    "get_current_user",
    "generate_password_hash",
    "check_password_hash",
    "SECRET_KEY",
    "jwt"
]
