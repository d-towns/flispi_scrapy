from sqlalchemy import create_engine, Column, String, Float, Enum
import enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class UnitTypeEnum(enum.Enum):
    SQFT = 'SQFT'
    UNIT = 'UNIT'
    LOT = 'LOT'
    LFT = 'LFT'
    EACH = 'EACH'

class ServiceItemEntity(Base):
    __tablename__ = 'service_item'
    
    name = Column(String, nullable=False, primary_key=True)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    unit = Column(Float, nullable=False)
    unit_type = Column(Enum(UnitTypeEnum), nullable=False)


