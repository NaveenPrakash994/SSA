from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use the correct database URL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Aren@localhost:5432/sudoku_solver"

# Database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class to define models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
