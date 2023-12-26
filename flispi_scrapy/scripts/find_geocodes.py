import googlemaps
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_dirty, flag_modified

import sys
from pathlib import Path

parent_dir = Path(__file__).resolve().parent.parent

# Add the 'flispi_scrapy' directory to sys.path
sys.path.append(str(parent_dir))

# Now you can import the PropertyEntity from sql.property
from models.sql.property import PropertyEntity

gmaps = googlemaps.Client(key='AIzaSyDNQz71iokW0F045lNGGa514dZj9PGhx6E')

connection_string = "sqlite:///landbank_properties.sqlite"
engine = create_engine(connection_string, echo=True)
Session = sessionmaker(bind=engine)
session = Session(bind=engine)

properties = session.query(PropertyEntity).all()

# Delete all properties with no parcel_id
# for property_ in properties:
#     if property_.parcel_id == 'None':
#         session.delete(property_)  
#         flag_dirty(property_)
#         session.commit()


# take the first 10 properties for testing]

# Get the coordinates for each property by is address using the Google Maps geocode API and then update the property coords in the database
for property_ in properties:
    if property_.address == None or property_.city == None or property_.zip == None or property_.address == 'None' or property_.city == 'None' or property_.zip == 'None' or property_.coords != None:
        continue
    address = property_.address + ', ' + property_.city + ', ' + property_.zip
    print(address)
    geocode_result = gmaps.geocode(address)
    if geocode_result.__len__() != 0:
        print('geocode_result WAS FOUND', geocode_result[0]['geometry']['location'])
        if geocode_result.__len__() > 0:
            property_.coords = geocode_result[0]['geometry']['location']
            flag_modified(property_, 'coords')
            session.commit()
        else:
            print('No geocode result for', address)
    else:
        print('geocode_result WAS NOT FOUND')
        print('No geocode result for', address)

session.close()