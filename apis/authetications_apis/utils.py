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


def validate_access_token(authorization: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    if authorization.scheme == "Bearer": 
        try:
            payload = jwt.decode(authorization.credentials, JWT_ACCESS_SECRET_KEY, ALGORITHM)

        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        expires_at = payload.get("expire_at")
        # Convert the string to a datetime object
        expires_datetime = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S.%f")
        current_utc = datetime.datetime.utcnow()
        print("here")
        if current_utc > expires_datetime:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Access token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # token correct return the payload
        return payload
    
    else:
        raise HTTPException(
            status_code=401, 
            detail="Invalid scheme"
        )
    

def validate_refresh_token(authorization: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    if authorization.scheme == "Bearer": 
        try:
            payload = jwt.decode(authorization.credentials, JWT_REFRESH_SECRET_KEY, ALGORITHM)

        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        expires_at = payload.get("expire_at")
        # Convert the string to a datetime object
        expires_datetime = datetime.datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S.%f")
        current_utc = datetime.datetime.utcnow()
        if current_utc > expires_datetime:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # token correct return user email
        return payload.get("email")
    
    else:
        raise HTTPException(
            status_code=401, 
            detail="Invalid scheme"
        )
