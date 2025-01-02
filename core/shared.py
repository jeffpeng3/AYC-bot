from aiohttp import ClientSession

client: ClientSession | None = None


async def get_client() -> ClientSession:
    global client
    if not client:
        client = ClientSession()
    return client


async def close_client():
    global client
    if client:
        await client.close()
        client = None
