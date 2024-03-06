import pandas as pd
from sqlalchemy import create_engine
import uuid
import os
from dotenv import load_dotenv

from ..models.scrapy.property import Property
load_dotenv()

class LandbankScraperPipeline(object):
    def __init__(self):
        environment = os.environ.get('ENV', 'development')
        db_url = os.environ['PROD_POSTGRESS_URL'] if environment != 'development' else os.environ['DEV_POSTGRESS_URL']
        self.engine = create_engine(db_url)
        self.parcel_ids = self._load_parcel_ids()

    def _load_parcel_ids(self):
        """Load parcel IDs from the database into a set for faster lookup."""
        result = pd.read_sql_query("SELECT parcel_id FROM properties", self.engine)
        return set(result['parcel_id'].tolist())

    def process_item(self, item, spider):
        if isinstance(item, Property):
            if item['parcel_id'] not in self.parcel_ids:
                self._insert_property(item)
                self.parcel_ids.add(item['parcel_id'])
                print(f"{item['parcel_id']} saved to database")
            else:
                print('Parcel ID already exists in the database')
        return item

    def _insert_property(self, item):
        """Insert a new property item into the database."""
        try:
            # Prepare data for insertion
            data = {
                'id': str(uuid.uuid4()),
                'parcel_id': item['parcel_id'],
                'address': item['address'],
                'city': item['city'],
                'zip': item['zip'],
                'property_class': item['property_class'],
                'featured': False,
                # Assuming other fields are initialized to None by default
            }
            df = pd.DataFrame([data])
            df.to_sql('properties', self.engine, if_exists='append', index=False)
        except Exception as e:
            print(f"Error saving {item['parcel_id']} to database: {e}")

