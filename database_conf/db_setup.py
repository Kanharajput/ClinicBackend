from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv


# load the env variable
load_dotenv()

# initialise the variables
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_NAME = os.getenv('DATABASE_NAME')

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# it's instance is the real 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models classes
Base = declarative_base()

# return the session which already exists
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()