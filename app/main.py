from fastapi import FastAPI
from app.database import init_db
from app.routers import registry, escrow
from app.config import settings
import logging

logging.basicConfig(level=settings.LOG_LEVEL)

app = FastAPI(title="Agent Economy Engine API")

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(registry.router)
app.include_router(escrow.router)

@app.get("/")
async def root():
    return {"message": "Agent Economy Engine PoC is running"}
