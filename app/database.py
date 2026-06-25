from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

# Create the db connection engine using the database URL from the settings
engine = create_engine(settings.database_url)

# The sessionmaker factory generates new Session objects when called.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define a base class for the ORM models to inherit from
class Base(DeclarativeBase):
    pass

# Dependency function to get a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()