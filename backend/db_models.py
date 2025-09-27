from sqlalchemy import create_engine, Column, String, Text, ForeignKey, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid

#Dinh nghia cac bang trong db

Base = declarative_base()

class Section(Base):
    __tablename__ = "sections"
    section_id = Column(UUID(as_uuid=True), primary_key=True, default = uuid.uuid4)
    section_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    #Dinh nghia khoa ngoai
    context_items = relationship("ContextItem", back_populates="section")
    
class ContextItem(Base):
    __tablename__ = "context_items"
    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.section_id"))
    summary_text = Column(Text)
    version = Column(Integer, default=1) #lan update thu may?
    created_at = Column(DateTime, default=func.now())
    
    section = relationship("Section", back_populates="context_items")
