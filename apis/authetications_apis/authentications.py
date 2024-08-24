from fastapi import APIRouter, Depends, HTTPException
from database_conf.db_setup import get_session
from schemas.users import Registration, UserDetails, Login
from models.users import User
from sqlalchemy import select, update
from .utils import get_hashed_password, verify_password, create_access_token, create_refresh_token
import requests
import os
from dotenv import load_dotenv


#  api router for authentications
auth_api = APIRouter()

# load the env variable
load_dotenv()

# initialise the variables
APIIP_SECRET_KEY = os.getenv('APIIP_SECRET_KEY')


@auth_api.post("/registration")
async def user_registration(user_data:Registration, session = Depends(get_session)):
    # check email and password are not empty strings
    if user_data.email == "" or user_data.password == "":
        raise HTTPException(406, "Email or password can't be empty")
    
    # check email uniqueness
    email_existance_query = select(User).filter_by(email=user_data.email)
    email_existance = session.execute(email_existance_query).scalar()

    if email_existance:
        raise HTTPException(406, "Email already exists")
    
    # start creating a new user
    user = User()
    user.email = user_data.email
    # store the hashed password
    user.password = get_hashed_password(user_data.password)

    # generate and save user access and refresh token
    # later this will be removed
    access_token, refresh_token = create_access_token(user.email), create_refresh_token(user.email)
    user.access_token = access_token
    user.refresh_token = refresh_token

    try:
        # save user to the database
        session.add(user)
        session.commit()  
        user = user.row2dict(user)
        return user

    except Exception as e:
        print(e)
        raise HTTPException(500, "Something went wrong")
    
    finally:
        session.close()
    

@auth_api.patch("/register-user-details/{user_id}")
async def user_details_registration(user_id:int, user_data:UserDetails, session = Depends(get_session)):
    # check user exists or not
    user_query = select(User).filter_by(id=user_id)
    user = session.execute(user_query).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # update user if exists
    user_update_query = update(User).where(User.id == user_id).values(
        first_name = user_data.first_name,
        last_name = user_data.last_name,
        phone_number = user_data.phone_number,
        current_role = user_data.current_role,
        specialisation = user_data.specialisation
    )

    try:
        session.execute(user_update_query)
        session.commit()

    except Exception as e:
        print(e)
        raise HTTPException(500, "Something went wrong")
    
    finally:
        session.close()
    
    return {"details":"user details updated successfully"}


@auth_api.post("/login")
async def user_login(user_data:Login, session = Depends(get_session)):
    # check email exists or not
    email_exists_query = select(User).filter_by(email=user_data.email)
    user = session.execute(email_exists_query).scalar()
    user_id = user.id
    
    if not user:
        raise HTTPException(404, "Email not found")
    
    if not verify_password(user_data.password,user.password):
        print("Password not matches")
        raise HTTPException(401, "Password not matches")
    
    # generate access and refresh token
    access_token, refresh_token = create_access_token(user.email), create_refresh_token(user.email)

    store_token_query = update(User).where(User.id == user.id).values(access_token=access_token, refresh_token=refresh_token)

    # execute the query 
    try:
        session.execute(store_token_query)
        session.commit()

    except Exception as e:
        print(e)
        raise HTTPException(500, "Something went wrong")
    
    finally:
        session.close()

    return {"access_token": access_token, "refresh_token": refresh_token, "user_id":user_id}


@auth_api.post("/register-user-country/{user_id}")
async def register_user_country(user_id:int, user_ip:str, session = Depends(get_session)):
    # Define API URL
    API_URL = f"https://apiip.net/api/check?accessKey={APIIP_SECRET_KEY}"

    # Enter the ip for search
    IP_FOR_SEARCH = f"&ip={user_ip}"

    # Getting in response JSON
    res = requests.get(API_URL+IP_FOR_SEARCH)

    # Loading JSON from text to object
    user_data = res.json()

    # check for errors
    if "success" in user_data:
        if not user_data["success"]:
            return user_data["message"]
            
    user_country = user_data["countryName"]

    update_country_query = update(User).where(User.id==user_id).values(country=user_country)

    # execute the query 
    try:
        session.execute(update_country_query)
        session.commit()

    except Exception as e:
        print(e)
        raise HTTPException(500, "Something went wrong")

    return {"country": user_country}


@auth_api.get("/get-full-name/{user_id}")
async def register_user_country(user_id:int, session = Depends(get_session)):
    full_name_query = select(User.first_name, User.last_name).filter_by(id=user_id)
    
    # execute the query 
    full_name_list = session.execute(full_name_query).fetchall()
    if not full_name_list:
        raise HTTPException(404, f"No user found with id {user_id}")
    
    try:
        session.commit()
        return {"full_name": full_name_list[0][0] + " " + full_name_list[0][1]}

    except Exception as e:
        print(e)
        raise HTTPException(500, "Something went wrong")
