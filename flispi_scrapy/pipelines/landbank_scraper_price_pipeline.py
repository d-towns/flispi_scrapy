from sqlalchemy import create_engine, INTEGER
from sqlalchemy.orm import sessionmaker

from flispi_scrapy.models.sql.property import PropertyEntity

import googlemaps
import os
from dotenv import load_dotenv
load_dotenv()

gmaps = googlemaps.Client(key=os.environ['GOOGLE_API_KEY'])

class LandbankPriceScraperPipeline(object):
    def open_spider(self, spider):
        #Get specific environment variables
        db_url = os.environ['PROD_POSTGRESS_URL'] if os.environ['ENV'] != 'development' else os.environ['DEV_POSTGRESS_URL']

        self.connection_string = db_url
        self.engine = create_engine(self.connection_string)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def close_spider(self, spider):
        self.session.close()

    def process_item(self, item, spider):
        # Find the property based on parcelId and update its price
        print('item in pipline', item)
        property_ = self.session.query(PropertyEntity).filter_by(parcel_id=item['parcel_id']).first()

        if property_.coords == None:
            address = property_.address + ', ' + property_.city + ', ' + property_.zip
            print(address)
            geocode_result = gmaps.geocode(address)
            if geocode_result.__len__() != 0:
                print('geocode_result WAS FOUND', geocode_result[0]['geometry']['location'])
                if geocode_result.__len__() > 0:
                    property_.coords = geocode_result[0]['geometry']['location']
                else:
                    print('No geocode result for', address)
            else:
                print('geocode_result WAS NOT FOUND')
                print('No geocode result for', address)
        print(item)
        if property_:
            property_.price =  int(item.get('price',0))
            property_.square_feet = int(item.get('square_feet', 0))
            property_.bedrooms = int(item.get('bedrooms', 0))
            property_.bathrooms = int(item.get('bathrooms', 0))
            property_.year_built = item.get('year_built', None)
            property_.lot_size = float(item.get('lot_size', 0))
            property_.stories = int(item.get('stories', 0))
            property_.garage = item.get('garage', None)
            property_.features = item.get('features', None)
            property_.images = item.get('images', None)
            property_.exterior_repairs = item.get('exterior_repairs', None)
            property_.interior_repairs = item.get('interior_repairs', None)
            property_.next_showtime = item.get('next_showtime', None)
            self.session.commit()
        
        return item


