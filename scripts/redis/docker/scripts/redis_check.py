import redis
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Now you can use the environment variables
password = os.getenv('REDIS_PASSWORD')

# Connect to Redis on localhost and the default port 6379
r = redis.Redis(host='localhost', port=6379, db=1, password=password)

# Set a key
r.set('mykey', 'myvalue')

# Get the value of a key
value = r.get('mykey')
print(f"Value after insertion: {value}")

# Delete the key
r.delete('mykey')

value = r.get('mykey')
print(f"Value after deletion: {value}")