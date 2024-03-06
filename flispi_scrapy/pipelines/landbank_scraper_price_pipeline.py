from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import googlemaps
import os
from dotenv import load_dotenv
from flispi_scrapy.models import PropertyEntity
load_dotenv()

gmaps = googlemaps.Client(key=os.environ['GOOGLE_API_KEY'])

class LandbankPriceScraperPipeline(object):
    def __init__(self):
        environment = os.environ.get('ENV', 'development')
        db_url = os.environ['PROD_POSTGRESS_URL'] if environment != 'development' else os.environ['DEV_POSTGRESS_URL']
        self.engine = create_engine(db_url)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def open_spider(self, spider):
        self.session = self.Session()

    def close_spider(self, spider):
        self.session.close()
        self.Session.remove()

    def process_item(self, item, spider):
        print(f'item in price pipeline: {item}')
        property_ = self.session.query(PropertyEntity).filter_by(parcel_id=item['parcel_id']).first()

        if property_ is None:
            print('Property not found')
            return item

        if item['not_available']:
            self.session.delete(property_)
            print(f"{item['parcel_id']} no longer available, deleted from database")
            self.session.commit()
            return item

        self._update_property(property_, item)
        self.session.commit()
        return item

    def _update_property(self, property_, item):
        if property_.coords is None:
            self._geocode_property(property_)

        for field in ['price', 'square_feet', 'bedrooms', 'bathrooms', 'stories']:
            setattr(property_, field, int(item.get(field, 0)))

        for field in ['year_built', 'garage', 'features', 'images', 'exterior_repairs', 'interior_repairs', 'next_showtime']:
            setattr(property_, field, item.get(field))

        property_.lot_size = float(item.get('lot_size', 0))

    def _geocode_property(self, property_):
        address = f"{property_.address}, {property_.city}, {property_.zip}"
        print(address)
        try:
            geocode_result = gmaps.geocode(address)
            if geocode_result:
                property_.coords = geocode_result[0]['geometry']['location']
                print(f'geocode_result FOUND: {property_.coords}')
            else:
                print(f'No geocode result for {address}')
        except Exception as e:
            print(f'Geocoding error for {address}: {e}')
