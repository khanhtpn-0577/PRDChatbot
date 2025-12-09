from sqlalchemy import create_engine, Column, String, Text, ForeignKey, Integer, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid
from sqlalchemy import Enum

#Dinh nghia cac bang trong db

Base = declarative_base()

class Section(Base):
    __tablename__ = "sections"
    section_id = Column(UUID(as_uuid=True), primary_key=True, default = uuid.uuid4)
    section_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    #Dinh nghia khoa ngoai
    context_items = relationship("ContextItem", back_populates="section")
    prd = relationship("PRD", back_populates="section")
    messages = relationship("Message", back_populates="section", cascade="all, delete-orphan")
    
class Message(Base):
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.section_id"), nullable=False)
    
    role = Column(Enum("user", "assistant", name="message_role"), nullable=False)
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=func.now())

    # Relationship
    section = relationship("Section", back_populates="messages")

class ContextItem(Base):
    __tablename__ = "context_items"
    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.section_id"))
    summary_text = Column(Text)
    version = Column(Integer, default=1) #lan update thu may?
    created_at = Column(DateTime, default=func.now())
    
    section = relationship("Section", back_populates="context_items")
    
    
class PRD(Base):
    __tablename__ = "prds"
    prd_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.section_id"), nullable=False)
    prd_text = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    section = relationship("Section", back_populates="prd")
    architecture = relationship("Architecture", back_populates="prd", cascade="all, delete-orphan") # Quan he 1-n voi Architecture, khi xoa PRD thi xoa Architecture lien quan
    features = relationship("Feature", back_populates="prd", cascade="all, delete-orphan")
    
class Feature(Base):
    __tablename__ = "features"
    feature_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prd_id = Column(UUID(as_uuid=True), ForeignKey("prds.prd_id"), nullable=False)
    
    title = Column(String, nullable=False)
    user_story = Column(Text, nullable=False)
    business_value = Column(String)
    priority_moscow = Column(Enum("Must", "Should", "Could", "Wont", name="moscow_priority"), nullable=False)
    
    status = Column(Enum("Active", "Removed", name="feature_status"), default="Active")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    prd = relationship("PRD", back_populates="features")
    
    
class Architecture(Base):
    __tablename__ = "architectures"
    architecture_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prd_id = Column(UUID(as_uuid=True), ForeignKey("prds.prd_id"), nullable=False)
    architecture_text = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    prd = relationship("PRD", back_populates="architecture")
    plan = relationship("Plan", back_populates="architecture", cascade="all, delete-orphan")
    
class Plan(Base):
    __tablename__ = "plans"
    plan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    architecture_id = Column(UUID(as_uuid=True), ForeignKey("architectures.architecture_id"), nullable=False)
    plan_text = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    architecture = relationship("Architecture", back_populates="plan")

