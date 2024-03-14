import uuid
from sqlalchemy import Column, String, Float, INTEGER, JSON, BOOLEAN, DATETIME, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from .property import PropertyEntity
from .service_item import ServiceItemEntity

Base = declarative_base()

class PropertyServiceItemEntity(Base):
    __tablename__ = 'property_service_item'

    id = Column('id', String, primary_key=True, default=uuid.uuid4) 
    property_id = Column('property_id', String, ForeignKey(PropertyEntity.id))
    service_item_id = Column('service_item_id', String, ForeignKey(ServiceItemEntity.name))