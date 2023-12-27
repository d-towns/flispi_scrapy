import pandas as pd
from sqlalchemy import create_engine
import sqlite3
import uuid
import os
from dotenv import load_dotenv

from ..models.scrapy.property import Property
load_dotenv()

class LandbankScraperPipeline(object):
    def __init__(self):
        # db_url = os.environ['PROD_POSTGRESS_URL'] if os.environ['NODE_ENV'] != 'development' else os.environ['DEV_POSTGRESS_URL']
        db_url = os.environ['PROD_POSTGRESS_URL']
        print('db_url', db_url)


        self.connection_string = db_url
        self.engine = create_engine(self.connection_string)
        # get all of the parcel IDs from the database and store them in a list in self.parcel_ids
        self.parcel_ids = pd.read_sql_query("SELECT parcel_id FROM properties", self.engine)['parcel_id'].tolist()

    def process_item(self, item, spider):
        print('item in pipline', item)
        if isinstance(item, Property):
            df = pd.DataFrame({
                'id': [str(uuid.uuid4())], # new UUID field
                'parcel_id': [item['parcel_id']], # remove spaces from parcelId
                'address': [item['address']],
                'city': [item['city']],
                'zip': [item['zip']],
                'property_class': [item['property_class']],
                'featured' : False,
                'price': None,
                'square_feet': None,
                'bedrooms': None,
                'bathrooms': None,
                'year_built': None,
                'lot_size': None,
                'stories': None,
                'garage': None,
                'features': None,
                'coords': None
            })
            # if the parcel ID already exists in the db, do not save
            # if the parcel ID does not exist in the db, save
            if item['parcel_id'] in self.parcel_ids:
                print('Parcel ID already exists in the database')
            else:
                df.to_sql('properties', self.engine, if_exists='append', index=False)
                print(item['parcel_id'], 'saved to database')
        return item