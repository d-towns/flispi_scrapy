from scrapy.cmdline import execute

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
print('Running main.py')
execute(['scrapy', 'crawl', 'landbank_spider'])
execute(['scrapy', 'crawl', 'price_spider'])

