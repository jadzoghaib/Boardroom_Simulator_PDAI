import httpx
import asyncio
async def test():
    async with httpx.AsyncClient() as client:
        res = await client.post('http://127.0.0.1:8001/api/boardroom_turn', json={'thread_id':'testerr2','budget':0,'burn_rate':0,'revenue':0,'founder_experience':0,'sector':'string','pitch':'string','action':'start'})
        print(res.status_code)
        print(res.text)
asyncio.run(test())
