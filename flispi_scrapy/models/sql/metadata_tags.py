import uuid
from sqlalchemy import Column, String, Float, INTEGER, JSON, BOOLEAN, DATETIME, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from .property import PropertyEntity
from .service_item import ServiceItemEntity

Base = declarative_base()

class MetadataTagEntity(Base):
    name = Column('name', String)