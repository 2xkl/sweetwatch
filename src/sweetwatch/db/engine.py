from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sweetwatch.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)
