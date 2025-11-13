from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RegisterDTO(BaseModel):
    userID: str
    name: str
    password: str

class loginDTO(BaseModel):
    