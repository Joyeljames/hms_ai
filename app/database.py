from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os


#load env
load_dotenv()
# 3. Get DATABASE_URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

# 4. Create engine (the translator)
engine = create_engine(DATABASE_URL)

# 5. Create SessionLocal (session factory)
SessionLocal = sessionmaker(autocommit = False,autoflush=False,bind=engine)

# 6. Create Base (model template

Base = declarative_base()



# 7. Create get_db function (session manager)
def get_db():

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    