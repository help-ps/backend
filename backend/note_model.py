from pydantic import BaseModel

class Note(BaseModel):
    userID : str
    NoteID : str
    title: str
    content: str

class NewNoteDTO(BaseModel):
    userID : str
    title: str
    content: str

class UpdateNoteDTO(BaseModel):
    NoteID : str
    title: str
    content: str

class DeleteNoteDTO(BaseModel):
    NoteID : str