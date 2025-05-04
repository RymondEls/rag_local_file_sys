from pydantic import BaseModel, Field
from datetime import datetime

class QueryInput(BaseModel):
    question: str
    session_id: str = Field(default=None)
    model: str = Field(default="mistralai/mistral-7b-instruct:free")  # Модель по умолчанию

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: str  # Динамическая модель

class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int