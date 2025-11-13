from fastapi import FastAPI, HTTPException
from models.note import Note
import uuid ,os
from pymongo import MongoClient
from dotenv import load_dotenv

app = FastAPI()



load_dotenv(dotenv_path=".env")  
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database("memo_save")
notes_collection = db["notes"]

@app.get("/check_uri")
def check_uri():
    return {"MONGO_URI": os.getenv("MONGO_URI")} #uri 잘 가져오는지 보는 디버그용 코드 

@app.post("/notes/")
def create_note(note: Note):
    new_note = note.dict()
    # new_note["id"] = str(uuid.uuid4())
    notes_collection.insert_one(new_note)
    return {"message": "메모 저장", "note": new_note}


@app.get("/notes/")
def get_notes():
    try:
        notes = list(notes_collection.find({}, {"_id": 0}))
        return {"notes": notes}
    except Exception as e:
        return {"error": str(e)}


@app.put("/notes/{note_id}")
def update_note(note_id: str, updated_note: Note):
    result = notes_collection.update_one(
        {"id": note_id},
        {"$set": updated_note.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없음")
    return {"message": "메모 수정", "note": updated_note.dict()}


@app.delete("/notes/{note_id}") 
def delete_note(note_id: str):
    result = notes_collection.delete_one({"id": note_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없음")
    return {"message": "메모 삭제", "note_id": note_id}

