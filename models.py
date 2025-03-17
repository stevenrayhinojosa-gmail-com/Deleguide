from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

# Create database engine
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    goals = Column(String, nullable=False)  # Comma-separated string
    needs = Column(String, nullable=False)  # Comma-separated string
    tasks = relationship("Task", back_populates="student")

class Staff(Base):
    __tablename__ = 'staff'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    expertise = Column(String, nullable=False)  # Comma-separated string
    tasks = relationship("Task", back_populates="staff_member")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    staff_id = Column(Integer, ForeignKey('staff.id'))
    student_id = Column(Integer, ForeignKey('students.id'))
    deadline = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    
    staff_member = relationship("Staff", back_populates="tasks")
    student = relationship("Student", back_populates="tasks")

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(bind=engine)

# Function to get database session
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
