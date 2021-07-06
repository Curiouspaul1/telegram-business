import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
# URL = "https://smebot-tg.herokuapp.com/"
api_secret = os.getenv('API_SECRET')
api_key = os.getenv('API_KEY')
sendgrid_key = os.getenv('SENDGRID_API_KEY')
sender_email = os.getenv('SENDER_EMAIL')
FAUNA_KEY = os.getenv('FAUNA_KEY')
