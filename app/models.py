
from sqlalchemy import Column, Integer, String
from .database import Base

class Upload(Base):
    __tablename__ = "sudoku_solver"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    solved_image_path = Column(String)

