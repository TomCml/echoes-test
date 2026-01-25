"""
Echoes Backend - API v1 Router
Aggregates all API endpoint routers.
"""
from fastapi import APIRouter

from src.presentation.api.v1 import auth, players, combat, inventory, monsters, dungeons, leaderboard

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(players.router, prefix="/players", tags=["Players"])
api_router.include_router(combat.router, prefix="/combat", tags=["Combat"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
api_router.include_router(monsters.router, prefix="/monsters", tags=["Monsters"])
api_router.include_router(dungeons.router, prefix="/dungeons", tags=["Dungeons"])
api_router.include_router(leaderboard.router, prefix="/leaderboard", tags=["Leaderboard"])
