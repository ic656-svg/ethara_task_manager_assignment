import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Grab the raw URL from the environment
raw_db_url = os.getenv("DATABASE_URL")

# If the variable is missing OR empty, default to SQLite
if not raw_db_url:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./taskmanager.db"
else:
    # SQLAlchemy requires 'postgresql://' but some cloud providers give 'postgres://'
    if raw_db_url.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
    else:
        SQLALCHEMY_DATABASE_URL = raw_db_url

# SQLite requires a specific argument to allow multiple threads to interact with it
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()