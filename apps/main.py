from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app import model, utils
from app.database import SessionLocal, engine, Base






# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener")

# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/shorten")
def shorten_url(long_url: str, db: Session = Depends(get_db)):
    # Generate short code
    short_code = utils.generate_short_code()
    
    # Check if already exists
    db_url = db.query(model.URL).filter(model.URL.short_code == short_code).first()
    while db_url:  # regenerate if duplicate
        short_code = utils.generate_short_code()
        db_url = db.query(model.URL).filter(model.URL.short_code == short_code).first()

    # Save in DB
    new_url = model.URL(long_url=long_url, short_code=short_code)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    return {"short_url": f"http://127.0.0.1:8000/{short_code}"}

@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    db_url = db.query(model.URL).filter(model.URL.short_code == short_code).first()
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(db_url.long_url)

from flask import Flask, Blueprint
from database import init_db

