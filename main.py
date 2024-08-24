from fastapi import FastAPI
from database_conf.db_setup import Base, engine
from apis.authetications_apis.authentications import auth_api
from apis.payment_apis.cashfree_apis import payment_api
from apis.ai_apis.all_ai_apis import ai_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register authetications apis
app.include_router(auth_api)
app.include_router(payment_api)
app.include_router(ai_router)

# Push all the new changes to the db
Base.metadata.create_all(engine)