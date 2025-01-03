import os

token = os.getenv('token')
server_ip = os.getenv('server_ip')
weather_api = os.getenv('weather_api')

calendar_username = os.getenv('calendar_username')
calendar_password = os.getenv('calendar_password') 
nextcloud_url = os.getenv('nextcloud_url')

anilist_access_token = os.getenv('anilist_access_token')
    #this is for getting token

client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')

path_to_langchain = os.getenv('path_to_langchain')
user_name = os.getenv('user_name')
db_password = os.getenv('db_password')
host_name = os.getenv('host_name')
db_name = os.getenv('db_name')

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east-1")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")