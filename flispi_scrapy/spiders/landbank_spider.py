import scrapy

from ..models.scrapy.property import Property
from ..models.sql.property import PropertyEntity
from scrapy.exceptions import CloseSpider
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import re
from twisted.internet import asyncioreactor
asyncioreactor.install()
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose
from ..models.util.repair_costs import RepairCostsSingleton
from scrapy.linkextractors import LinkExtractor


# This class is responsible for scraping the landbank website for property data
# The data is then stored in the database
# The class is split into two spiders, one for scraping the property data and the other for scraping the price data
# The price data is scraped from the property details page
# The property details page is accessed by following the link to the featured property page
# The featured property page contains more detailed information about the property

class LandBankSpider(scrapy.Spider):
    name = 'landbank_spider'
    # allowed_domains = ['thelandbank.org']
    start_urls = ['https://www.thelandbank.org/find_properties.asp?LRCsearch=setdo']

    custom_settings = {
        'ITEM_PIPELINES': {
            'flispi_scrapy.pipelines.landbank_scraper_pipeline.LandbankScraperPipeline': 300
        }
    }

    # print('Starting Landbank Spider', start_urls)   

    def parse(self, response):
        print('Parsing Landbank Spider', response)
        for row in response.xpath('//tr'):
            loader = ItemLoader(item=Property(), selector=row)
            loader.default_output_processor = TakeFirst()

            loader.add_xpath('parcel_id', './td[1]/label/a/text()', MapCompose(lambda x: x.replace('-', '')))
            loader.add_xpath('address', './td[2]/div/text()')
            loader.add_xpath('city', './td[3]/div/text()')
            loader.add_xpath('zip', './td[4]/div/text()')
            loader.add_xpath('property_class', './td[5]/div/text()')

            yield loader.load_item()

        # Handling pagination
        next_page = response.xpath('//a[contains(@href, "javascript:document.LRCquery.LRCpage.value=\'next\';document.LRCquery.submit();")]')
        if next_page:
            yield scrapy.FormRequest.from_response(
                response,
                formname='LRCquery',
                formdata={'LRCpage': 'next', 'LRCsearch': 'redo'},
                callback=self.parse
            )

class PriceSpider(scrapy.Spider):
    name = 'price_spider'
    custom_settings = {
        'ITEM_PIPELINES': {
            'flispi_scrapy.pipelines.landbank_scraper_price_pipeline.LandbankPriceScraperPipeline': 300,
        }
    }
    start_urls = ['https://www.thelandbank.org/featured_homes.asp', 'https://www.thelandbank.org/readyforrehab.asp', 'https://www.thelandbank.org/featured_lots.asp']
    # start_urls = ['https://www.thelandbank.org/featured_homes.asp']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        load_dotenv()
        print('Starting Price Spider\n\n')
        environment = os.environ.get('ENV', 'development')
        db_url = os.environ['PROD_POSTGRESS_URL'] if environment != 'development' else os.environ['DEV_POSTGRESS_URL']
        if not db_url:
            raise CloseSpider('Database URL not set in environment variables.')
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        self.session = Session()
        self.link_extractor = LinkExtractor(allow_domains='thelandbank.org', allow=r'/featuredprop_fm\.asp\?pid=\d+')
        
        self.parcel_ids = self.load_parcel_ids()

    # def start_requests(self):
    #     for pid in self.parcel_ids:
    #         url = f'https://www.thelandbank.org/property_sheet.asp?pid={pid}&loc=2&from=main'
            
    #         yield scrapy.Request(url=url, callback=self.parse, meta={'parcel_id': pid})
    #     # yield scrapy.Request(url='https://www.thelandbank.org/property_sheet.asp?pid=4119380013&loc=2&from=main', 
    #     #     callback=self.parse,
    #     #     meta={'parcel_id': '4119380013'})


    # Grab the data on the search details page (property_sheet.asp)
    def load_parcel_ids(self):
        try:
            parcel_ids = [row.parcel_id for row in self.session.query(PropertyEntity.parcel_id).all()]
            return parcel_ids
        except Exception as e:
            self.logger.error(f"Failed to load parcel IDs: {e}")
            raise CloseSpider('Failed to load parcel IDs from the database.')
        
    def parse(self, response):
        print('Parsing Price Spider', response)
        # get all the links from the page

        for link in self.link_extractor.extract_links(response):
            # make a request to the link
            print('\n\nLink:', link)
            yield response.follow(link, callback=self.extract_featured_data)


        # parcel_id = response.meta['parcel_id']
        # print(f'Processing property details for Parcel ID #: {parcel_id}')
        # starting_price = response.xpath('//table[@class="infotab"]/tr[1]/td[2]/text()').get()
        # price = self.extract_price(starting_price)
        # print(f'Price: {price} \n\n')
        # property_item = Property(parcel_id=response.meta['parcel_id'], price=price)

        # property_not_available = response.xpath("//h2[contains(text(), 'Property Not Availiable')]/text()").get()

        # property_item.update({'not_available': True if property_not_available else False})
        # if property_not_available: 
        #     yield property_item
        #     return

        # featured_link = response.xpath("//a[contains(text(), 'featured')]/@href").get()

        # if featured_link:
        #     # Follow the link to the featured property page and grab more info
        #     yield scrapy.Request(url='https://www.thelandbank.org/' + featured_link, callback=self.extract_featured_data, meta={'property_item': property_item})
        # else:
        #     yield property_item

    # Grab the data on the featured details page (featuredproperty.asp)
    def extract_featured_data(self, response):
        # Follow the link to the featured property page and grab more info
        
        # callback funciton for processing property page reapair description to the official ServiceItem list in the db
        property_item = Property(parcel_id=response.url.split('=')[-1], price=None)
    

        print(f'Processing featured property details for Parcel ID #: {property_item["parcel_id"]}')
        repair_mappings = RepairCostsSingleton().get_repair_mappings()
        def map_repair_string(repair_string):
            repair_list = repair_mappings.get(repair_string, [])
            return repair_list
            
        # property_details = response.meta['property_item']
        property_item.update({
            'featured': True,
            'exterior_repairs': self.extract_list_items(response.xpath("//article[@id='content']/ul[position()=1]/li"), map_repair_string),
            'interior_repairs': self.extract_list_items(response.xpath("//article[@id='content']/ul[position()=2]/li"), map_repair_string),
            'images': self.extract_images(response),
            'next_showtime': self.extract_next_showtime(response),
            'price': self.extract_featured_price(response) if not property_item['price'] else property_item['price'],
            **self.extract_property_features(response),
        })
        print(property_item)
        # print(property_details)
        property_item.update({'not_available': False})
        yield property_item

    
    # FEATURED DATA HELPER FUNCTIONS
    
    def extract_price(self, price_str):
        if price_str and '$' in price_str:
            return int(price_str.replace('$', '').replace(',', '').strip())
        return None

    def extract_featured_price(self, response):
        suggested_offer_price = response.xpath("//h3[contains(text(), 'Starting Offer')]/text()").get()
        print('\n\nSuggested Offer Price:', suggested_offer_price)
        if suggested_offer_price and 'negotiable' not in str(suggested_offer_price).lower():
            suggested_offer_price = int(float(suggested_offer_price.split(':')[1].replace(',', '').replace("$", "").strip()))
            return int(suggested_offer_price)
        return 0
    
    def extract_list_items(self, selector, callback):
        print(selector)
        if callback:
            return [item for li in selector for item in callback(li.xpath('normalize-space(.)').get())]
        else:
            return [li.xpath('normalize-space(.)').get() for li in selector]
    def extract_images(self, response):
        images = response.xpath("//a[@class='sslightbox']/@href | //div[@class='bss-slides ccss1']/figure/img/@src").getall()
        return ['https://www.thelandbank.org/' + img if not img.startswith('http') else img for img in images]
    
    def extract_next_showtime(self, response):
        next_showtime = response.xpath("//p[contains(text(), '2025')]/text()").get()
        if next_showtime:
            match = re.search(r'(\w+,\s+\w+\s+\d{1,2},\s+\d{4});\s+(\d{1,2}:\d{2}\s+[ap]\.m\.)', next_showtime)
            if not match:
                match = re.search(r'(\w+,\s+\w+\s+\d{1,2},\s+\d{4});\s+(\d{1,2}:\d{2}\s+[ap]\.m\.)\s*-\s*(\d{1,2}:\d{2}\s+[ap]\.m\.)', next_showtime)
            if match:
                date_to_parse = match.group(1) + ' ' + match.group(2)
                date_string = date_to_parse.replace('p.m.', 'PM').replace('a.m.', 'AM')
                date_object = datetime.strptime(date_string, '%A, %B %d, %Y %I:%M %p')
                return date_object
            else:
                print("SHOWTIME: Date and time format not recognized")
        return None
    
    def extract_property_features(self, response):
        features = {}

        property_info_list = response.xpath("//div[@class='2u 12u']/ul")
        for li in property_info_list.xpath('./li'):
            text = li.xpath('normalize-space(.)').get()
            if 'Square feet' in text:
                features['square_feet'] = int(text.split('Square feet')[1].strip())
            elif 'Bedrooms' in text or "Bedroom" in text:
                text.replace('s', '')
                features['bedrooms'] = int(text.split('Bedroom')[0].strip())
            elif 'Bathroom' in text or "Bathrooms" in text:
                text.replace('s', '')
                features['bathrooms'] = int(text.split('Bathroom')[0].strip())
            elif 'Year built:' in text:
                features['year_built'] = text.split('Year built:')[1].strip()
            elif 'Acres' in text:
                features['lot_size'] = float(text.split('Acres')[0].strip())
            elif 'Stories:' in text:
                features['stories'] = int(text.split('Stories')[0].strip())
            elif 'Garage' in text:
                features['garage'] = text.split('Garage')[0].strip()
        return features 

# settings = get_project_settings()
# runner = CrawlerRunner(settings)
# configure_logging(settings)
# @defer.inlineCallbacks
# def crawl():
#     print('Running crawl')
#     # yield runner.crawl(LandBankSpider)
#     yield runner.crawl(PriceSpider)
#     sys.exit()
    


# if __name__ == 'flispi_scrapy.spiders.landbank_spider' and not reactor.running:
#     crawl()
#     reactor.run() 