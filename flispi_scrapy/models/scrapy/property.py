# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class Property(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    parcel_id = scrapy.Field()
    address = scrapy.Field()
    city = scrapy.Field()
    zip = scrapy.Field()
    property_class = scrapy.Field()
    price = scrapy.Field()
    square_feet = scrapy.Field()
    featured = scrapy.Field()
    bedrooms = scrapy.Field()
    bathrooms = scrapy.Field()
    year_built = scrapy.Field()
    lot_size = scrapy.Field()
    stories = scrapy.Field()
    garage = scrapy.Field()

    coords = scrapy.Field()
    # Todo: Images should be a table with a many to one relationship to properties. the record should have the filename for an ftp server or s3 bucket
    images = scrapy.Field()
    next_showtime = scrapy.Field()
    exterior_repairs = scrapy.Field()
    interior_repairs = scrapy.Field()
    not_available = scrapy.Field()
    repair_cost = scrapy.Field()
