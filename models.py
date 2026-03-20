from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
from datetime import datetime

class CodeFile(Base):
    __tablename__ = "code_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    language = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    notes = Column(Text, default="")
    ai_overview = Column(Text, default="")
    date_imported = Column(DateTime, default=datetime.utcnow)

class Snippet(Base):
    __tablename__ = "snippets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    tags = Column(String(500), default="")
    source_file = Column(String(255), default="")
    source_file_id = Column(Integer, default=None)
    date_saved = Column(DateTime, default=datetime.utcnow)