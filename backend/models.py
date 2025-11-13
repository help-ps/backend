from pydantic import BaseModel

class LoginDTO(BaseModel):
    userID: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class signupDTO(BaseModel):
    userID: str
    password: str

class ImagePayload(BaseModel):
    filename: str
    image_base64: str  # Base64로 인코딩된 이미지 문자열

class streakDTO(BaseModel):
    userID: str