import scrapy

from ..models.scrapy.property import Property
from ..models.sql.property import PropertyEntity

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
            parcel_id = row.xpath('./td[1]/label/a/text()').get(default="").replace('-', '')
            address = row.xpath('./td[2]/div/text()').get()
            city = row.xpath('./td[3]/div/text()').get()
            zip_code = row.xpath('./td[4]/div/text()').get()
            property_class = row.xpath('./td[5]/div/text()').get()

            if parcel_id:
                yield Property(
                    parcel_id=parcel_id,
                    address=address,
                    city=city,
                    zip=zip_code,
                    property_class=property_class,
                )

        next_page_js = response.xpath('//a[contains(@href, "javascript:document.LRCquery.LRCpage.value=\'next\';document.LRCquery.submit();")]')
        if next_page_js:
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
            'flispi_scrapy.pipelines.landbank_scraper_price_pipeline.LandbankPriceScraperPipeline': 300
        }
    }

    def start_requests(self):
        load_dotenv()

        # #Get specific environment variables
        prod_db_url = os.environ['PROD_POSTGRESS_URL']
        self.engine = create_engine(prod_db_url)
        Session = sessionmaker(bind=self.engine)
        with Session() as session:
            parcel_ids = [row.parcel_id for row in session.query(PropertyEntity.parcel_id).all() if row.parcel_id not in ('0', 'None')]
        for pid in parcel_ids:
            url = 'https://www.thelandbank.org/property_sheet.asp?pid={pid}&loc=2&from=main'
            yield scrapy.Request(url=url, callback=self.parse, meta={'parcel_id': pid})
        
        # Test Url
        # yield scrapy.Request(url='https://www.thelandbank.org/property_sheet.asp?pid=4626153017&loc=2&from=main', 
        #     callback=self.parse,
        #     meta={'parcel_id': '4626153017'})

    # Grab the data on the search details page (property_sheet.asp)
    def parse(self, response):
        starting_price = response.xpath('//table[@class="infotab"]/tr[1]/td[2]/text()').get()
        price = self.extract_price(starting_price)

        link = response.xpath("//a[contains(text(), 'featured')]/@href").get()
        property_item = Property(parcel_id=response.meta['parcel_id'], price=price)

        # Extract the href attribute from the selected <a> tag
        if link:
            # Follow the link to the featured property page and grab more info
            yield scrapy.Request(url='https://www.thelandbank.org/' + link, callback=self.extract_featured_data, meta={'property_item': property_item})
        else:
            yield property_item

    # Grab the data on the featured details page (featuredproperty.asp)
    def extract_featured_data(self, response):
        # Follow the link to the featured property page and grab more info
        # Select the div by class name, then the ul within it
        
        # yield property_details
        property_details = response.meta['property_item']
        property_details.update({
            'featured': True,
            'exterior_repairs': self.extract_list_items(response.xpath("//article[@id='content']/ul[position()=1]/li")),
            'interior_repairs': self.extract_list_items(response.xpath("//article[@id='content']/ul[position()=2]/li")),
            'images': self.extract_images(response),
            'next_showtime': self.extract_next_showtime(response),
            'price': self.extract_featured_price(response) if not property_details['price'] else property_details['price'],
            **self.extract_property_features(response),
        })
        print(property_details)
        yield property_details

    
    # FEATURED DATA HELPER FUNCTIONS
    
    def extract_price(self, price_str):
        if price_str and '$' in price_str:
            return int(price_str.replace('$', '').replace(',', '').strip())
        return 0

    def extract_featured_price(self, response):
        suggested_offer_price = response.xpath("//h2[contains(text(), 'Starting Offer')]/text()").get()
        if suggested_offer_price and 'negotiable' not in str(suggested_offer_price).lower():
            suggested_offer_price = int(suggested_offer_price.split(':')[1].replace(',', '').replace("$", "").strip())
            return int(suggested_offer_price)
        return 0
    
    def extract_list_items(self, selector):
        return [li.xpath('normalize-space(.)').get() for li in selector]

    def extract_images(self, response):
        images = response.xpath("//a[@class='sslightbox']/@href | //div[@class='bss-slides ccss1']/figure/img/@src").getall()
        return ['https://www.thelandbank.org/' + img if not img.startswith('http') else img for img in images]
    
    def extract_next_showtime(self, response):
        next_showtime = response.xpath("//p[contains(text(), '2024')]/text()").get()
        if next_showtime:
            match = re.search(r'(\w+,\s+\w+\s+\d{1,2},\s+\d{4});\s+(\d{1,2}:\d{2}\s+[ap]\.m\.)', next_showtime)
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
            if 'Square feet:' in text:
                features['square_feet'] = int(text.split('Square feet:')[1].strip())
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