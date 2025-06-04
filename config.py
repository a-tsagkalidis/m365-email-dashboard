import os
from dotenv import load_dotenv

if os.path.exists('.env.maildash.api'):
    load_dotenv(dotenv_path='.env.maildash.api')

class Config:
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')
    TENANT_ID = os.getenv('TENANT_ID')

app_config = Config()