import os
from dotenv import load_dotenv


if os.path.exists('.env.maildash.api'):
    load_dotenv('.env.maildash.api')

class Config:
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')
    MS_ONLINE_URL = os.getenv('MSONLINE_URL', 'https://login.microsoftonline.com')
    SECRET_KEY = os.getenv('SECRET_KEY')
    REDIRECT_PATH = '/getAToken'
    SCOPE = ['Mail.Read', 'Mail.Send']

app_config = Config()
