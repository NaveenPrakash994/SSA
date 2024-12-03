from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.sudoku_solver import solve_sudoku
import os
from app.models import Upload
import time

# Initialize FastAPI app
app = FastAPI()
Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "app/static/uploads"
SOLVED_DIR = "app/static/solved"  # Directory for solved images

# Initialize templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Ensure upload directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SOLVED_DIR, exist_ok=True)

# Define a route to render the upload page
@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate file type (optional, to ensure it's an image)
    if not file.filename.endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        # Save file locally
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        with open(filepath, "wb") as f:
            f.write(await file.read())

        # Solve Sudoku
        solved_filename = f"solved_{file.filename}"
        solved_filepath = os.path.join(SOLVED_DIR, solved_filename)
        solve_sudoku(filepath, solved_filepath)

        # Save metadata to database
        upload = Upload(filename=file.filename, solved_image_path=f"uploads/solved/{solved_filename}")
        db.add(upload)
        db.commit()
        db.refresh(upload)

        # Redirect to results page
        return RedirectResponse(url="/results/", status_code=303)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the file: {str(e)}")

@app.get("/results/", response_class=HTMLResponse)
async def results_page(request: Request, db: Session = Depends(get_db)):
    try:
        # Get the latest upload record from the database
        latest_upload = db.query(Upload).order_by(Upload.id.desc()).first()

        # If no upload is found, return an error
        if not latest_upload:
            raise HTTPException(status_code=404, detail="No results found.")

        return templates.TemplateResponse("results.html", {
            "request": request,
            "original_image": f"/static/{latest_upload.filename}",
            "solved_image": f"/static/{latest_upload.solved_image_path}"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching the results: {str(e)}")
