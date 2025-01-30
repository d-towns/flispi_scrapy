from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from flispi_scrapy.spiders.landbank_spider import LandBankSpider, PriceSpider

def run_spiders():
    process = CrawlerProcess(get_project_settings())
    # process.crawl(LandBankSpider)
    process.crawl(PriceSpider)
    process.start()  # Blocks here until all spiders are finished

if __name__ == '__main__':
    print('Running main.py')
    run_spiders()
    print('Spiders finished')
    import sys
    sys.exit()
