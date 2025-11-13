import os
import base64
import bcrypt
import uvicorn
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from models import LoginDTO, Token, signupDTO, ImagePayload, streakDTO
from fastapi import FastAPI, HTTPException, status

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
        "streak": 0
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

    from Search import Circle2Search
    result = Circle2Search(save_path)
    return {"result": result}

@app.get("/Search/tag_Search/{query}")
async def tag_search(query: str, n: int = 5):
    from Search import tag_Search
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
        {"$inc": {"streak": 1}}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"message": f"Streak updated successfully, now {user.get('streak')}"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)