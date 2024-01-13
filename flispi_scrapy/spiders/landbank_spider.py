import scrapy

from ..models.scrapy.property import Property
from ..models.sql.property import PropertyEntity

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
import re
from twisted.internet import asyncioreactor
asyncioreactor.install()
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings


class LandBankSpider(scrapy.Spider):
    name = 'landbank_spider'
    start_urls = ['https://www.thelandbank.org/find_properties.asp?LRCsearch=setdo']
    custom_settings = {
        'ITEM_PIPELINES': {
            'flispi_scrapy.pipelines.landbank_scraper_pipeline.LandbankScraperPipeline': 300
        }
    }

    def parse(self, response):
        for row in response.xpath('//tr'):
            property_item = Property()
            property_item['parcel_id'] = str(row.xpath('./td[1]/label/a/text()').get()).replace('-','')
            property_item['address'] = row.xpath('./td[2]/div/text()').get()
            property_item['city'] = row.xpath('./td[3]/div/text()').get()
            property_item['zip'] = row.xpath('./td[4]/div/text()').get()
            
            property_item['property_class'] = row.xpath('./td[5]/div/text()').get()
            if(property_item['parcel_id']):
                yield property_item
        

        # Handle pagination
        next_link_exists = response.xpath('//a[contains(@href, "javascript:document.LRCquery.LRCpage.value=\'next\';document.LRCquery.submit();")]').get()
        print('Pagination Found, executing...', next_link_exists)
        if next_link_exists:
            formdata = {
                'LRCpage': 'next',
                'LRCsearch': 'redo',
            }

            yield scrapy.FormRequest.from_response(
                response,
                formname='LRCquery',  # replace with actual form name
                formdata=formdata,
                callback=self.parse
            )

class PriceSpider(scrapy.Spider):
    name = 'price_spider'
    custom_settings = {
        'ITEM_PIPELINES': {
            'flispi_scrapy.pipelines.landbank_scraper_price_pipeline.LandbankPriceScraperPipeline': 300
        }
    }

    def start_requests(self):
        load_dotenv()

        # #Get specific environment variables
        prod_db_url = os.environ['PROD_POSTGRESS_URL']
        self.connection_string = prod_db_url
        self.engine = create_engine(self.connection_string)
        Session = sessionmaker(bind=self.engine)
        session = Session()
        parcel_ids = [row.parcel_id for row in session.query(PropertyEntity.parcel_id).all() if row.parcel_id != '0' and row.parcel_id != 'None']
        session.close()
        # Test Url
        # yield scrapy.Request(url='https://www.thelandbank.org/property_sheet.asp?pid=4119176011&loc=2&from=main', 
        #     callback=self.parse,
        #     meta={'parcel_id': '4119176011'})
        for pid in parcel_ids:
        #     # Assuming parcelId is a unique identifier, construct the URL
        #     # https://www.thelandbank.org/property_sheet.asp?pid=0404300022&loc=2&from=main
            yield scrapy.Request(url='https://www.thelandbank.org/property_sheet.asp?pid=' + str(pid) + '&loc=2&from=main', 
                        callback=self.parse, 
                        meta={'parcel_id': pid})

    # Grab the data on the search details page (property_sheet.asp)
    def parse(self, response):
        starting_price = response.xpath('//table[@class="infotab"]/tr[1]/td[2]/text()').get()

        link_selector = response.xpath("//a[contains(text(), 'featured')]/@href")
        property_item = Property()
        property_item['parcel_id'] = response.meta['parcel_id']

        if starting_price:
            if '$' in starting_price:
                starting_price = int(starting_price.replace('$', '').replace(',', '').strip())
                property_item['price'] = starting_price
            else:
                property_item['price'] = 0


        # Extract the href attribute from the selected <a> tag
        link = link_selector.get()
        if(link):
            # Follow the link to the featured property page and grab more info
            yield scrapy.Request(url='https://www.thelandbank.org/' + link, callback=self.extract_featured_data, meta={'property_item': property_item})
        else:
            yield property_item

    # Grab the data on the featured details page (featuredproperty.asp)
    def extract_featured_data(self, response):
        # Follow the link to the featured property page and grab more info
        # Select the div by class name, then the ul within it
        print('extract_featured_data', response)
        property_details = response.meta['property_item']
        property_details['featured'] = True
        property_info_list = response.xpath("//div[@class='2u 12u']/ul")
        suggested_offer_price = response.xpath("//h2[contains(text(), 'Starting Offer')]/text()").get()
        next_showtime = response.xpath("//p[contains(text(), '2023')]/text()").get()
        exterior_repairs_text = response.xpath("//article[@id='content']/ul[position()=1]")
        interior_repairs_text = response.xpath("//article[@id='content']/ul[position()=2]")

        exterior_repairs = []
        interior_repairs = []
        
        if exterior_repairs_text.xpath('./li'):
            for li in exterior_repairs_text.xpath('./li'):
                text = li.xpath('normalize-space(.)').get()
                exterior_repairs.append(text)
            property_details['exterior_repairs'] = interior_repairs

        if interior_repairs_text.xpath('./li'):
            for li in interior_repairs_text.xpath('./li'):
                text = li.xpath('normalize-space(.)').get()
                interior_repairs.append(text)
            property_details['interior_repairs'] = exterior_repairs

        if next_showtime:
            match = re.search(r'(\w+,\s+\w+\s+\d{1,2},\s+\d{4});\s+(\d{1,2}:\d{2}\s+[ap]\.m\.)', next_showtime)
            if match:
                date_to_parse = match.group(1) + ' ' + match.group(2)
                date_string = date_to_parse.replace('p.m.', 'PM').replace('a.m.', 'AM')
                date_object = datetime.strptime(date_string, '%A, %B %d, %Y %I:%M %p')
                property_details['next_showtime'] = date_object
            else:
                print("SHOWTIME: Date and time format not recognized")


        # Initialize a dictionary to hold the extracted property details

        if suggested_offer_price and 'negotiable' not in str(suggested_offer_price).lower():
            suggested_offer_price = int(suggested_offer_price.split(':')[1].replace(',', '').replace("$", "").strip())
            property_details['price'] = int(suggested_offer_price)

        carousel_div = response.xpath("//div[@class='bss-slides ccss1']/div")
        lightbox_a_tag = response.xpath("//a[@class='sslightbox']/@href")


        for tag in lightbox_a_tag:
            image = tag.get()
            if image:
                if 'http' not in image:
                    image = 'https://www.thelandbank.org/' + image
                if 'images' not in property_details:
                    property_details['images'] = []
                property_details['images'].append(image)

        for figure in carousel_div.xpath('./figure'):
            image = figure.xpath('./img/@src').get()
            if image:
                if 'http' not in image:
                    image = 'https://www.thelandbank.org/' + image
                if 'images' not in property_details:
                    property_details['images'] = []
                property_details['images'].append(image)


        property_features = {}

        # Iterate over all the li tags within the ul
        for li in property_info_list.xpath('./li'):
            # Extract the text content of each li tag
            text = li.xpath('normalize-space(.)').get()

            # Check for specific keywords and extract the data
            if 'Square feet:' in text:
                property_details['square_feet'] = int(text.split('Square feet:')[1].strip())
            elif 'Bedrooms' in text:
                property_details['bedrooms'] = int(text.split('Bedrooms')[0].strip())
            elif 'Bathrooms' in text:
                property_details['bathrooms'] = int(text.split('Bathrooms')[0].strip())
            elif 'Year built:' in text:
                property_details['year_built'] = text.split('Year built:')[1].strip()
            elif 'Acres' in text:
                property_details['lot_size'] = float(text.split('Acres')[0].strip())
            elif 'Stories:' in text:
                property_details['stories'] = int(text.split('Stories')[0].strip())
            elif 'Garage' in text:
                property_details['garage'] = text.split('Garage')[0].strip()
            else:
                property_features[text] = True
        
        yield property_details
settings = get_project_settings()
runner = CrawlerRunner(settings)
configure_logging(settings)
@defer.inlineCallbacks
def crawl():
    yield runner.crawl(LandBankSpider)
    yield runner.crawl(PriceSpider)
    reactor.stop()


crawl()
reactor.run() 