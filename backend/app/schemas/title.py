from pydantic import BaseModel
from typing import Optional

class TitleCreate(BaseModel):
    title_name: str

class TitleRead(BaseModel):
    title_id: int
    title_name: str

    class Config:
        from_attributes = True

class TitleUpdate(BaseModel):
    title_name: Optional[str] = None

    class Config:
        from_attributes = True
