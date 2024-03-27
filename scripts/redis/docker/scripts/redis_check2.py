import asyncio
import redis
import tracemalloc
from dotenv import load_dotenv
from redis import asyncio as aioredis
import os


# Enable tracemalloc
tracemalloc.start()

# Load the .env file
load_dotenv()

# # Now you can use the environment variables
# password = os.getenv("REDIS_PASSWORD")

# # Connect to Redis on localhost and the default port 6379
# r = aioredis.StrictRedis(
#     host='localhost',
#     port='6379',
#     db='1',
#     password=password,
# )

# # Set a key
# r.set("mykey", "myvalue")

# # Get the value of a key
# value = r.get("mykey")
# print(f"Value after insertion: {value}")

# # Delete the key
# r.delete("mykey")

# value = r.get("mykey")
# print(f"Value after deletion: {value}")

# Now you can use the environment variables
password = os.getenv("REDIS_PASSWORD")


async def main():
    # Connect to Redis on localhost and the default port 6379
    r = aioredis.StrictRedis(
        host="localhost",
        port="6379",
        db="1",
        username="root",
        password=password,
    )

    # Set a key
    await r.set("mykey", "myvalue")

    exist = await r.exists(f"mykey")
    print(f"Value exist: {exist}")

    # Get the value of a key
    value = await r.get("mykey")
    print(f"Value after insertion: {value}")

    # Delete the key
    await r.delete("mykey")

    value = await r.get("mykey")
    print(f"Value after deletion: {value}")


# Run the main coroutine
asyncio.run(main())
