import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.env import get_env
from app.core.db.setup import setup_db

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],  # Or ["http://localhost:3000"] for stricter control
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEBUG = get_env("DEBUG", "True") == "True"
PORT = int(get_env("PORT", "8000")) or 8000


def run_app():
    setup_db()
    uvicorn.run("app:app", reload=DEBUG, port=PORT, host="0.0.0.0")
