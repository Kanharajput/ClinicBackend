from passlib.context import CryptContext
import datetime
from datetime import timedelta
import jwt 
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from jwt import PyJWTError


# Define the OAuth2 scheme
security = HTTPBearer()

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
JWT_ACCESS_SECRET_KEY = "1@)^t%@cbjim%@$@&^@&%^&RFghgjvbd#$@ty23!"   # should be kept secret
JWT_REFRESH_SECRET_KEY = "u@*g%3@*&fdfgh@#$%^@&jkl45@#*tg5y3$&("
ACCESS_TOKEN_EXPIRE_MINUTES = 30             # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)
    

def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def create_access_token(email: str):
    # generate the when token expires
    expires_delta = str(datetime.datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    data_to_encode = {"expire_at": expires_delta, "email": email}

    try:
        encoded_token = jwt.encode(data_to_encode, JWT_ACCESS_SECRET_KEY, ALGORITHM)

    except Exception as e:
        print(e)
        raise HTTPException(500, "Internal Server error")    

    return encoded_token


def create_refresh_token(email: str):
    # generate the when token expires   
    expires_delta = str(datetime.datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    data_to_encode = {"expire_at": expires_delta, "email": email}

    try:
        encoded_token = jwt.encode(data_to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)

    except Exception as e:
        print(e)
        raise HTTPException(500, "Internal Server error")

    return encoded_token


def authorize_user(authorization: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    if authorization.scheme == "Bearer": 
        try:
            payload = jwt.decode(authorization.credentials, JWT_ACCESS_SECRET_KEY, ALGORITHM)
            return payload
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    else:
        raise HTTPException(
            status_code=401, 
            detail="Invalid scheme"
        )

