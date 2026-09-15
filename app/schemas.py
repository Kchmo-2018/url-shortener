from datetime import datetime
from pydantic import BaseModel, HttpUrl


class URLCreateRequest(BaseModel):
    target_url: HttpUrl


class URLResponse(BaseModel):
    short_code: str
    short_url: str
    target_url: str
    created_at: datetime
    click_count: int

    class Config:
        from_attributes = True
