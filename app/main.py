from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.sudoku_solver import solve_sudoku
from app.models import Upload
import os
import logging

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "app/static/uploads"
SOLVED_DIR = "app/static/solved"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SOLVED_DIR, exist_ok=True)

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        # Validate file type
        if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            raise HTTPException(status_code=400, detail="Invalid file type. Only PNG, JPG, and JPEG are allowed.")

        # Save uploaded file
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        with open(filepath, "wb") as f:
            f.write(await file.read())

        # Solve Sudoku and save solved image
        solved_filename = f"solved_{file.filename}"
        solved_filepath = os.path.join(SOLVED_DIR, solved_filename)
        
        try:
            solve_sudoku(filepath, solved_filepath)
        except Exception as solve_error:
            logger.error(f"Sudoku solving failed: {solve_error}")
            os.remove(filepath)  # Remove the uploaded file
            raise HTTPException(status_code=422, detail=f"Sudoku solving failed: {str(solve_error)}")

        # Save upload record
        upload = Upload(filename=file.filename, solved_image_path=f"solved/{solved_filename}")
        db.add(upload)
        db.commit()
        db.refresh(upload)

        return RedirectResponse(url="/results/", status_code=303)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected upload error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during file upload")

@app.get("/results/", response_class=HTMLResponse)
async def results_page(request: Request, db: Session = Depends(get_db)):
    try:
        latest_upload = db.query(Upload).order_by(Upload.id.desc()).first()

        if not latest_upload:
            return templates.TemplateResponse("results.html", {
                "request": request,
                "error": "No results found"
            })

        return templates.TemplateResponse("results.html", {
            "request": request,
            "original_image": f"/static/uploads/{latest_upload.filename}",
            "solved_image": f"/static/solved/{os.path.basename(latest_upload.solved_image_path)}"
        })

    except Exception as e:
        logger.error(f"Results page error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving results")
