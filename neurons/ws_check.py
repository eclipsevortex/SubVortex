import asyncio
from subnet.api.subvortex_api import SubVortexApi

ws = SubVortexApi()

async def run():
    await ws.send({'key': 'subs:5Grp2YwtJNYpQEzVGpZBypYnbM6PXZui6xmU2a23JEfyKpNo:5H3da4na4hyUWDS7zWceXawkeunociv2D3hdqzG1J32AEdtG', 'ip': '158.220.84.119'})

if __name__ == "__main__":
    # Use asyncio.run() to run the async function
    asyncio.run(run())