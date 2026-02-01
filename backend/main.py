import os
from fastapi import FastAPI
from infisical_sdk import InfisicalSDKClient

# Imports from the new layered architecture
from app.api.routes.items import router as items_router
from app.api.routes.battle import router as battle_router
from app.api.routes.login import router as login_router
from app.core.database import Base, engine

app = FastAPI()

client = InfisicalSDKClient(host=os.getenv("INFISICAL_API_URL"), token=os.getenv("INFISICAL_TOKEN"),)

app.include_router(items_router, prefix="/items", tags=["items"])
app.include_router(battle_router, prefix="/battle", tags=["battle"])
app.include_router(login_router, prefix="/login", tags=["login"])

@app.get("/health")
def health():
    db = client.secrets.get_secret_by_name(
        secret_name="DATABASE_URL",
        project_id="9edf2628-e6d1-4b45-a5d0-c5c7fde078a6",
        environment_slug="dev",
        secret_path="/"
        )
    if db.secretValue:
        return {"status": "ok"}
    else:
        return {"status": "ko"}
