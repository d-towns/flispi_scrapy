# Goals:
# 1. Implement a pipeline that processes items from 
    
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from openai import OpenAI
import os
from dotenv import load_dotenv
from ..models.sql.property import PropertyEntity
from ..models.sql.service_item import ServiceItemEntity, UnitTypeEnum
from ..models.sql.property_service_item import PropertyServiceItemEntity
load_dotenv()



class ImagePipeline(object):
    def __init__(self) -> None:
        environment = os.environ.get('ENV', 'development')
        db_url = os.environ['PROD_POSTGRESS_URL'] if environment != 'development' else os.environ['DEV_POSTGRESS_URL']
        self.engine = create_engine(db_url)
        self.session = scoped_session(sessionmaker(bind=self.engine))()
        self.client = OpenAI()
        
    def process_item(self, spider, item):
        item
        return 

    def get_image_tags(self):
        self.session.query()

    def get_image_context(self, image_url):
        
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What’s in this image? Five me the tags from this list that can be associated with the image: "},
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                    },
                    },
                ],
                }
            ],
            max_tokens=300,
            )
        return response.choices[0]

    def create_context_prompt(image_url):
        if 'zillow' in image_url:
            return 'zillow'
        elif 'realtor' in image_url:
            return 'realtor' 
        else:
            return 'other'
        


    response = self.client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {
        "role": "user",
        "content": [
            {"type": "text", "text": "What’s in this image?"},
            {
            "type": "image_url",
            "image_url": {
                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
            }, 
            },
        ],
        }
    ],
    max_tokens=300,
    )

    print(response.choices[0])