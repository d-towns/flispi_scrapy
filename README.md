# Flispi Scrapy

## Description
This is a simple scrapy project that scrapes the [Genesee County Land Bank](https://thelandbank.org) website and saves the data to a postgres database.

Due to the nature of the website, the scraper had to be written using two differnt spiders. The first spider scrapes the list of properties and the second spider scrapes the details of each property.

## Installation
1. Clone the repository
2. Install the requirements
3. Create a postgres database
4. Create a .env file in the root directory of the project and add the following variables:
    - PROD_POSTGRESS_URL
    - DEV_POSTGRESS_URL
    - GOOGLE_API_KEY
    - ENV
5. Start your virtual environment
6. Run the following command to start the scraper:
    - `scrapy crawl landbank_spider`
    

