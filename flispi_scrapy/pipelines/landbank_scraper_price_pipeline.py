from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import googlemaps
import os
import uuid
from dotenv import load_dotenv
from ..models.sql.property import PropertyEntity
from ..models.sql.service_item import ServiceItemEntity, UnitTypeEnum
from ..models.sql.property_service_item import PropertyServiceItemEntity
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
        for field in ['price']:
            if item.get(field) is not None:
                setattr(property_, field, float(item.get(field)))
        for field in [ 'square_feet', 'bedrooms', 'bathrooms', 'stories']:
            setattr(property_, field, int(item.get(field, 0)))

        for field in ['year_built', 'garage', 'featured', 'images', 'next_showtime', 'interior_repairs', 'exterior_repairs']:
            setattr(property_, field, item.get(field))
        total_repair_cost_min = float(0)
        total_repair_cost_max = float(0)
        for field in ['interior_repairs', 'exterior_repairs']:
            for service_item_name in item.get(field, []):
                service_item_entity = self.session.query(ServiceItemEntity).filter_by(name=service_item_name).first()
                
                # create property_service_item for each service_item
                if self.session.query(PropertyServiceItemEntity).filter_by(property_id=property_.id, service_item_id=service_item_entity.name).first() is None:
                    property_service_item = PropertyServiceItemEntity(id=uuid.uuid4(), property_id=property_.id, service_item_id=service_item_entity.name)
                    self.session.add(property_service_item)
                # add the average price of the service_item to the total_repair_cost
                
                if service_item_entity.unit_type == UnitTypeEnum.SQFT:
                    total_repair_cost_min += float(service_item_entity.min_price) * (float(property_.square_feet) / float(service_item_entity.unit))
                    total_repair_cost_max += float(service_item_entity.max_price) * float(property_.square_feet) / float(service_item_entity.unit)
                elif service_item_entity.unit_type == UnitTypeEnum.EACH:
                    total_repair_cost_min += float(service_item_entity.min_price)
                    total_repair_cost_max += float(service_item_entity.max_price)
        setattr(property_, 'repair_cost_max', total_repair_cost_max)
        setattr(property_, 'repair_cost_min', total_repair_cost_min)

        property_.lot_size = float(item.get('lot_size', 0))

    def _geocode_property(self, property_):
        address = f"{property_.address}, {property_.city}, {property_.zip}"
        try:
            geocode_result = gmaps.geocode(address)
            if geocode_result:
                property_.coords = geocode_result[0]['geometry']['location']
                print(f'geocode_result FOUND: {property_.coords}')
            else:
                print(f'No geocode result for {address}')
        except Exception as e:
            print(f'Geocoding error for {address}: {e}')