from model import Token, LoginDTO, signupDTO, ImagePayload, streakDTO
from note_model import Note, NewNoteDTO, UpdateNoteDTO, DeleteNoteDTO
from fastapi import FastAPI, HTTPException, status
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from Search import tag_Search, Circle2Search
from jose import jwt
import uvicorn
import base64
import bcrypt
import uuid
import os
import datetime

load_dotenv()

# --- 환경 변수 ---
MONGODB_URI = os.getenv("MONGODB_URI")
SECRET_KEY = os.getenv("SECRET_KEY")  # JWT 서명에 사용할 비밀 키
ALGORITHM = os.getenv("ALGORITHM", "HS256") # 사용할 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)) # 토큰 만료 시간(분)

app = FastAPI()

client = AsyncIOMotorClient(MONGODB_URI)
UserDB = client["UserDB"]
users_collection = UserDB["user_db"]

NoteDB = client.get_database("memo_save")
notes_collection = NoteDB["notes"]

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    JWT 액세스 토큰 생성
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 기본 만료 시간 (15분)
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.get("/")
async def main():
    return {"message": "Help-PS API"}

@app.post("/login", response_model=Token)
async def login(data: LoginDTO): 
    if not data.userID or not data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login failed: Missing required fields"
        )

    user = await users_collection.find_one({"userID": data.userID})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed: User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    plain_password_bytes = data.password.encode('utf-8')
    hashed_password_bytes = user["password"].encode('utf-8')

    if not bcrypt.checkpw(plain_password_bytes, hashed_password_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed: Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["userID"]}, expires_delta=access_token_expires
    )


    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/signup")
async def signup(data: signupDTO):
    existing_user = await users_collection.find_one({"userID": data.userID})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UserID already registered"
        )
    
    password_bytes = data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)
    hashed_password = hashed_password_bytes.decode('utf-8')
    new_user = {
        "userID": data.userID,
        "password": hashed_password,
        "created_at": str(datetime.date.today()),
        "streak": [0]
    }
    result = await users_collection.insert_one(new_user)
    return {"message": "User created successfully", "user_id": str(result.inserted_id)}

@app.get("/Search/Circle2Search")
async def circle2_search(data : ImagePayload):
    """
    Base64 인코딩된 이미지를 받아 Circle2Search 실행, 태그 반환
    """
    try:
        image_data = base64.b64decode(data.image_base64)
    except Exception as e:
        return {"error": "Invalid Base64 string", "details": str(e)}

    save_path = f"./uploaded_{data.filename}"
    with open(save_path, "wb") as f:
        f.write(image_data)

    result = Circle2Search(save_path)
    return {"result": result}

@app.get("/Search/tag_Search/{query}")
async def tag_search(query: str, n: int = 5):
    result = tag_Search(query, n)
    return {"result": result}

@app.post("/streak/update")
async def update_streak(data: streakDTO):
    """
    사용자 스트릭 업데이트
    """
    userID = data.userID
    user = await users_collection.find_one({"userID": data.userID})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing userID"
        )
    
    result = await users_collection.update_one(
    {"userID": userID},
    [{
        "$set": {
            "streak": {
                "$concatArrays": [{
                    "$slice": [
                        "$streak",
                        0,
                        {"$subtract": [{"$size": "$streak"}, 1]}
                    ]},
                    [1]
                ]
            }
        }
    }]
)

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"message": f"Streak updated successfully, now {user.get('streak')}"}

@app.post("/create_note")
async def create_note(data: NewNoteDTO):
    if not data.title or not data.content or not data.userID:
        raise HTTPException(status_code=400, detail="data 누락")
    
    user = await users_collection.find_one({"userID": data.userID})
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없음")
    
    new_note = {
        "userID": data.userID,
        "noteID": str(uuid.uuid4()),
        "title": data.title,
        "content": data.content
    }

    try:
        result = notes_collection.insert_one(new_note)
        # new_note["_id"] = str(result.inserted_id)
        return {"message": "메모 저장 성공", "note": new_note}
    except Exception as e:
        raise HTTPException(status_code=500, detail="메모 저장 실패")

@app.put("/notes/{note_id}")
async def update_note(data : UpdateNoteDTO):
    note = await notes_collection.find_one({"noteID": data.NoteID})
    if not note:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없음")

    notes_collection.update_one(
        {"noteID": data.NoteID}, 
        {"$set": {              
            "title": data.title,
            "content": data.content
        }}
    )

    return {"message": "메모 수정 성공"}

@app.delete("/notes/{note_id}") 
async def delete_note(data: DeleteNoteDTO):
    note_id = data.NoteID
    note = await notes_collection.find_one({"noteID": note_id})
    if not note:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없음")
    
    await notes_collection.delete_one({"noteID": note_id})
    
    return {"message": "메모 삭제", "noteID": note_id}

@app.post("/new_date")
async def new_date():
    result = await users_collection.update_many(
        {},
        {
            "$push": {
                "streak": 0
            }
        }
    )

    return {"message": f"Streaks updated for {result.modified_count} users"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)