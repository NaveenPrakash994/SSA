from fastapi import FastAPI, Depends, File, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from .database import engine, Base, get_db
from .models import File

# Initialize FastAPI app
app = FastAPI()

# Initialize database
Base.metadata.create_all(bind=engine)

# Mount templates and static directories
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routes
@app.get("/", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save file info in the database
    db_file = File(filename=file.filename)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Save the file to a static directory
    file_location = f"app/static/uploads/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    return {"filename": file.filename, "id": db_file.id}

@app.get("/results/", response_class=HTMLResponse)
def get_results(request: Request):
    # You can dynamically generate image paths or hard-code them for now
    return templates.TemplateResponse("results.html", {
        "request": request,
        "image1": "/static/uploads/image1.jpg",
        "image2": "/static/uploads/image2.jpg"
    })
