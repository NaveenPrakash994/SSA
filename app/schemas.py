from pydantic import BaseModel

class FileUploadSchema(BaseModel):
    filename: str
    file_path: str
