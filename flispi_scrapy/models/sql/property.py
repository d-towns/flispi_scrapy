import uuid
from sqlalchemy import Column, String, Float, INTEGER, Integer, JSON, Boolean, BOOLEAN, ARRAY, DATETIME
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class PropertyEntity(Base):
    __tablename__ = 'properties'
    
    id = Column(String, primary_key=True, default=uuid.uuid4)  # new UUID field
    parcel_id = Column(String, unique=True)  # no longer a primary key, but still unique
    address = Column(String, default=None)
    city = Column(String, default=None)
    zip = Column(String, default=None) # If zip codes can have leading zeroes or non-numeric characters, use String instead
    property_class = Column(String, default=None)
    price = Column(INTEGER, default=None)
    square_feet = Column(INTEGER, default=None)
    bedrooms = Column(INTEGER, default=None)
    bathrooms = Column(INTEGER, default=None)
    year_built = Column(String, default=None)
    lot_size = Column(Float, default=None)
    stories = Column(INTEGER, default=None)
    garage = Column(String, default=None)
    features = Column(JSON, default=None)
    featured = Column(BOOLEAN, default=False)
    coords = Column(JSON, default=None)
    images = Column(JSON, default=None)
    next_showtime = Column(DATETIME, default=None)
    interior_repairs = Column(JSON, default=None)
    exterior_repairs = Column(JSON, default=None)



