from fastapi import FastAPI, HTTPException
from models.note import Note
import json
import os
import uuid

app = FastAPI()
DATA_PATH = "data/notes.json" #일단은 json에 저장


def load_notes():
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w") as f:
            json.dump([], f)
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_notes(notes):
    with open(DATA_PATH, "w") as f:
        json.dump(notes, f, indent=4)


@app.post("/notes/")
def create_note(note: Note):
    notes = load_notes()
    new_note = note.dict()
    new_note["id"] = str(uuid.uuid4())
    notes.append(new_note)
    save_notes(notes)
    return {"message": "메모 저장", "note": new_note}


@app.get("/notes/")
def get_notes():
    notes = load_notes()
    return {"notes": notes}


@app.put("/notes/{note_id}")
def update_note(note_id: str, updated_note: Note):
    notes = load_notes()
    for i, n in enumerate(notes):
        if n["id"] == note_id:
            notes[i] = updated_note.dict()
            notes[i]["id"] = note_id
            save_notes(notes)
            return {"message": "메모 수정", "note": notes[i]}
    raise HTTPException(status_code=404, detail="메모를 찾을 수 없음")


@app.delete("/notes/{note_id}") 
def delete_note(note_id: str):
    notes = load_notes()
    for i, n in enumerate(notes):
        if n["id"] == note_id:
            deleted_note = notes.pop(i)
            save_notes(notes)
            return {"message": "메모 삭제", "note": deleted_note}
    raise HTTPException(status_code=404, detail="메모를 찾을 수 없음")
