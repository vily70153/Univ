import asyncio

import httpx


async def fetch_totals(
    client: httpx.AsyncClient,
    identifiers: list[int],
    concurrency: int = 4,
    retries: int = 2,
    timeout: float = 3,
) -> list[dict]:
    if concurrency < 1 or retries < 0 or timeout <= 0:
        raise ValueError("invalid concurrency, retries or timeout")
    semaphore = asyncio.Semaphore(concurrency)

    async def fetch(identifier: int) -> dict:
        for attempt in range(retries + 1):
            try:
                async with semaphore:
                    async with asyncio.timeout(timeout):
                        response = await client.get(
                            f"/orders/{identifier}/total", timeout=timeout
                        )
                        response.raise_for_status()
                        return response.json()
            except (httpx.TransportError, TimeoutError, httpx.HTTPStatusError) as exc:
                transient = not isinstance(
                    exc, httpx.HTTPStatusError
                ) or exc.response.status_code in {429, 502, 503, 504}
                if not transient or attempt == retries:
                    raise
                await asyncio.sleep(0.01 * 2**attempt)
        raise RuntimeError("unreachable")

    results = []
    # Bound both network concurrency and the number of allocated Tasks.
    for start in range(0, len(identifiers), concurrency):
        tasks: list[asyncio.Task[dict]] = [
            asyncio.create_task(fetch(i))
            for i in identifiers[start : start + concurrency]
        ]
        try:
            results.extend(await asyncio.gather(*tasks))
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    return results
