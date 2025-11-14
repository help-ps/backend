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
    image_base64: str

class streakDTO(BaseModel):
    userID: str

class tagSearchDTO(BaseModel):
    query : str
    n : int
