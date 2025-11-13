from fastapi import FastAPI, HTTPException
from model import Note, NewNoteDTO, UpdateNoteDTO, DeleteNoteDTO
import uuid ,os
from pymongo import MongoClient
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()  

MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client.get_database("memo_save")
notes_collection = db["notes"]

@app.get("/check_uri")
def check_uri():
    return {"MONGO_URI": str(os.getenv("MONGO_URI"))} #uri 잘 가져오는지 보는 디버그용 코드 

@app.post("/create_note")
def create_note(data: NewNoteDTO):
    if not data.title or not data.content or not data.userID:
        raise HTTPException(status_code=400, detail="data 누락")
    
    user = client.get_database("UserDB")["user_db"].find_one({"userID": data.userID})
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
        new_note["_id"] = str(result.inserted_id)
        return {"message": "메모 저장 성공", "note": new_note}
    except Exception as e:
        raise HTTPException(status_code=500, detail="메모 저장 실패")

@app.put("/notes/{note_id}")
def update_note(data : UpdateNoteDTO):
    note = notes_collection.find_one({"noteID": data.NoteID})
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
def delete_note(data: DeleteNoteDTO):
    note_id = data.NoteID
    note = notes_collection.find_one({"noteID": note_id})
    if not note:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없음")
    
    notes_collection.delete_one({"noteID": note_id})
    
    return {"message": "메모 삭제", "noteID": note_id}
