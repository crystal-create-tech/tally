from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.routers import shifts


app = FastAPI(title="Tally")
app.include_router(shifts.router)

@app.get("/health")
def health_check(db_session: Session = Depends(get_db_session)):
    db_session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}