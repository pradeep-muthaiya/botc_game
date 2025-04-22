import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

print('running database')

# Path to the SQLite database file inside the database_files folder
DATABASE_URL = "sqlite:///./database.db"

# Create the database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a base class for our models
Base = declarative_base()
#Base.metadata.create_all(bind=engine)
# Create a session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

