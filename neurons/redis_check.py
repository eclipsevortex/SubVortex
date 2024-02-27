import redis
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Now you can use the environment variables
password = os.getenv('REDIS_PASSWORD')
print(password)
# Connect to Redis on localhost and the default port 6379

r = redis.Redis(host='localhost', port=6379, db=0, password=password)

# Set a key
r.set('mykey', 'myvalue')

# Get the value of a key
value = r.get('mykey')
print(value)