import asyncio
import time

from fastapi import FastAPI

app = FastAPI()


async def wait_task(
  name: str,
  seconds: int      
):

    print(f'{name} 시작')

    await asyncio.sleep(seconds)

    print(f'{name} 종료')

    return f'{name} 완료'


@app.get('/basic')
async def basic():
    result = await wait_task(
        '작업 A',
        2
    )

    return {
        'result': result
    }



@app.get('/sequential')
async def sequential():

    start = time.perf_counter()

    result_a = await wait_task(
        '작업 A',
        2
    )

    result_b = await wait_task(
        '작업 B',
        2
    )

    elapsed = time.perf_counter() - start


    return {
        'result':[
            result_a,
            result_b
        ],
        'elapsed': round(elapsed, 2)
    }


@app.get('/parallel')
async def parallel():

    start = time.perf_counter()

    result_a, result_b = await asyncio.gather(
        wait_task(
            '작업 A',
            2
        ),
        wait_task(
            '작업 B',
            2
        )
    )


    elapsed = time.perf_counter() - start
    
    return {
        'result':[
            result_a,
            result_b
        ],
        'elapsed': round(elapsed, 2)
    }