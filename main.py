from passlib.context import CryptContext
from fastapi import FastAPI, Depends
from models import (RegisterDTO,loginDTO)
import pymongo
import os
import logging


pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
app = FastAPI()

@app.get("/")
def read_root():
    return {"mesage": "It is main page"}

@app.post("/register")
async def register(data: RegisterDTO):
    db_url = os.getenv("MONGODB_URI")
    db = pymongo.MongoClient(db_url)["UserDB"]
    users_collection = db["user_db"]

    if not data.userID or not data.password:
        return {"message" : f"Registration failed: Missing required fields for userID: {data.userID}"}
        

    hashed_password = pwd_context.hash(data.password)

    data = {
        "userID": data.userID,
        "name": data.name,
        "password": hashed_password,    
    }

    existing_user = await users_collection.find_one({"userID": data.get("userID")})

    if existing_user:
        return {"message" : f"Registration failed: User already exists - userID: {data.userID}"}
  

    await users_collection.insert_one(data)
    return {"message": f"User {data.get('userID')} signed up successfully!"}

@app.post("/login")
async def login(data : loginDTO):
    db_url = os.getenv("MONGODB_URI")
    db = pymongo.MongoClient(db_url)["UserDB"]
    users_collection = db["user_db"]

