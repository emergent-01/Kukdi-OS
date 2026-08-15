from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
import os
import logging

from database import client, db
from seed import seed
from routes import (calendar, conversation, dream, home, knowledge, memory,
                    people)

app = FastAPI(title="Kukdi — A Personal Operating System")

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"product": "Kukdi", "tagline": "A Personal Operating System", "status": "alive"}


@api_router.post("/seed")
async def reseed():
    return await seed(force=True)


app.include_router(api_router)
app.include_router(home.router, prefix="/api/home", tags=["home"])
app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])
app.include_router(memory.router, prefix="/api/memory", tags=["memory"])
app.include_router(dream.router, prefix="/api/dream", tags=["dream-offer"])
app.include_router(people.router, prefix="/api/people", tags=["people"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("kukdi")


@app.on_event("startup")
async def on_startup():
    result = await seed(force=False)
    logger.info(f"Kukdi startup seed: {result}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
