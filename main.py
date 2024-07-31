import datetime
from fastapi import FastAPI, Form, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import Column, Integer, String, Date, create_engine, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
import os


app = FastAPI()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 3307)
DB_NAME = os.getenv("DB_NAME")


DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Frnd(Base):
    __tablename__ = "frndlst"

    fid = Column(Integer, primary_key=True)
    name = Column(String(229), index=True)
    category = Column(String(222))
    dateofbirth = Column(Date, index=True)

class FrndResponse(BaseModel):

    fid: int
    name: str
    category: str
    dateofbirth: datetime.date
    act : str

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()

templates = Jinja2Templates(directory="templates")

def create_frnd(db: Session, name: str, category: str, dateofbirth: datetime.date):  
    db_frnd = Frnd(name=name, category=category, dateofbirth=dateofbirth)
    db.add(db_frnd)
    db.commit()
    db.refresh(db_frnd)
    db_frnd = db.query(Frnd).all()
    return db_frnd

def update_frnds(db: Session, name: str, category: str, dateofbirth: datetime.date):
    if Frnd.name == name:
       db_frnd = db.query(Frnd).filter(Frnd.name==name).first()
    elif Frnd.category == category:
        db_frnd = db.query(Frnd).filter(Frnd.category==category).first()
    else:
        db_frnd = db.query(Frnd).filter(Frnd.dateofbirth==dateofbirth).first()
    if not db_frnd:
        raise HTTPException(status_code =404, detail={"friend is not found"})
    db_frnd.name = name
    db_frnd.category = category
    db_frnd.dateofbirth = dateofbirth
    db.add(db_frnd)
    db.commit()
    db.refresh(db_frnd)
    db_frnd = db.query(Frnd).all()
    return db_frnd
    
 
def delete_row(db: Session, name: str): 
    db_frnd = db.query(Frnd).filter(Frnd.name==name).first()
    if not db_frnd:
        raise HTTPException(status_code =404, detail={"friend is not found"})
    db.delete(db_frnd)
    db.commit()
    db_frnd = db.query(Frnd).all()   
    return db_frnd


@app.get("/", response_class=HTMLResponse)
def read_form(request : Request):
    return templates.TemplateResponse("index.html", {"request": request})
    

@app.post("/cat")
def cat(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    dateofbirth: str = Form(...),
    act: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        date_of_birth = datetime.datetime.strptime(dateofbirth, '%Y-%m-%d').date()
        if act == "Add":
            result = create_frnd(db, name=name, category=category, dateofbirth=date_of_birth)
        elif act == "Update":
            result = update_frnds(db, name=name, category=category, dateofbirth=date_of_birth)
        elif act == "Delete":
            result = delete_row(db, name)
    except exc.SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return templates.TemplateResponse("index.html", {"request": request, "result" : result})





