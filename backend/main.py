import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Imports from the new layered architecture
from app.api.routes.items import router as items_router
from app.api.routes.battle import router as battle_router
from app.api.routes.login import router as login_router
from app.api.routes.inventory import router as inventory_router
from app.core.database import Base, engine

app = FastAPI(title="Echoes RPG", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items_router, prefix="/items", tags=["items"])
app.include_router(battle_router, prefix="/battle", tags=["battle"])
app.include_router(login_router, prefix="/login", tags=["login"])
app.include_router(inventory_router, tags=["inventory"])

@app.get("/health")
def health():
    return {"status": "ok"}
