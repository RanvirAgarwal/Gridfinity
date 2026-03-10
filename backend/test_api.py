import asyncio
from core.schemas import GenerateRequest
from pipeline.main import generate

async def test():
    req = GenerateRequest(prompt="A standard hex mesh tray")
    resp = await generate(req)
    print("SUCCESS:", resp.success)
    print("ERROR:", resp.error)

if __name__ == "__main__":
    asyncio.run(test())
