from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db_session


app = FastAPI(title="Tally")

@app.get("/health")
def health_check(db_session: Session = Depends(get_db_session)):
    db_session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}