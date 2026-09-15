import shortuuid
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine, get_db
from app.models import URL
from app.redis_client import redis_client
from app.schemas import URLCreateRequest, URLResponse

app = FastAPI(title="URL Shortener")

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    redis_client.ping()
    return {"status": "ok"}


@app.post("/api/urls", response_model=URLResponse)
def create_short_url(payload: URLCreateRequest, db: Session = Depends(get_db)):
    short_code = shortuuid.ShortUUID().random(length=7)
    url_entry = URL(short_code=short_code, target_url=str(payload.target_url))
    db.add(url_entry)
    db.commit()
    db.refresh(url_entry)

    return URLResponse(
        short_code=url_entry.short_code,
        short_url=f"{settings.base_url}/{url_entry.short_code}",
        target_url=url_entry.target_url,
        created_at=url_entry.created_at,
        click_count=url_entry.click_count,
    )


@app.get("/api/urls/{short_code}", response_model=URLResponse)
def get_url_info(short_code: str, db: Session = Depends(get_db)):
    url_entry = db.query(URL).filter(URL.short_code == short_code).first()
    if not url_entry:
        raise HTTPException(status_code=404, detail="Código no encontrado")

    return URLResponse(
        short_code=url_entry.short_code,
        short_url=f"{settings.base_url}/{url_entry.short_code}",
        target_url=url_entry.target_url,
        created_at=url_entry.created_at,
        click_count=url_entry.click_count,
    )


@app.get("/{short_code}")
def redirect_to_target(short_code: str, db: Session = Depends(get_db)):
    cached_target = redis_client.get(f"url:{short_code}")
    if cached_target:
        redis_client.incr(f"clicks:{short_code}")
        return RedirectResponse(
            url=cached_target,  # type: ignore
            status_code=307,
        )

    url_entry = db.query(URL).filter(URL.short_code == short_code).first()
    if not url_entry:
        raise HTTPException(status_code=404, detail="Código no encontrado")

    redis_client.setex(f"url:{short_code}", 3600, url_entry.target_url)

    url_entry.click_count += 1
    db.commit()

    return RedirectResponse(
        url=url_entry.target_url,
        status_code=307,
    )
