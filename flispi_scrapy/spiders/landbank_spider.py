import scrapy

from ..models.scrapy.property import Property

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
        print('does find js <a> tag', next_link_exists)
        if next_link_exists:
            formdata = {
                'LRCpage': 'next',
                'LRCsearch': 'redo',
                # you may need to include other form fields here
            }

            yield scrapy.FormRequest.from_response(
                response,
                formname='LRCquery',  # replace with actual form name
                formdata=formdata,
                callback=self.parse
            )


