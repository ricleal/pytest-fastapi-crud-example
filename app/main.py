import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import auth, models, user
from app.database import engine

# setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:8080",
]

# TODO Only add this CORS configuration if using a local environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # type: ignore
    allow_credentials=True,  # type: ignore
    allow_methods=["*"],  # type: ignore
    allow_headers=["*"],  # type: ignore
)

app.include_router(user.router, tags=["Users"], prefix="/api/users")

app.include_router(auth.router, tags=["Auth"], prefix="/api/auth")


@app.get("/api/healthchecker")
def root():
    return {"message": "The API is LIVE!!"}
