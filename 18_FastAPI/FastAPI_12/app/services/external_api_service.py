import asyncio
import httpx

class ExternalApiTimeoutError(Exception):
    """ """


class ExternalApiConnectionError(Exception):
    """ """

class ExternalApiStatusError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code



class ExternalApiService:

    def __init__(
            self,
            client: httpx.AsyncClient,
            base_url: str,
            delay_base_url: str
    ) -> None:

        self.client = client
        self.base_url = base_url.rstrip('/')
        self.delay_base_url =  delay_base_url.rstrip('/')


    async def _request_json(
            self,
            method: str,
            url: str,
            **kwargs
    ) -> dict:

        try:
            response = await self.client.request(
                method,
                url,
                **kwargs
            )

            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException as error:
            raise ExternalApiTimeoutError(
                status_code=error.response.status_code,
                message='외부 API 응답 시간이 초과되었습니다.'
            ) from error
        
        except httpx.HTTPStatusError as error:
            raise ExternalApiStatusError(
                status_code=error.response.status_code,
                message='외부 API가 오류 상태 코드를 반환했습니다.'
            ) from error

        except httpx.RequestError as error:
            raise ExternalApiConnectionError(
                status_code=error.response.status_code,
                message='외부 API에 연결할 수 없습니다.'
            ) from error


    async def get_post(self, post_id: int) -> dict:
        url = f'{self.base_url}/posts/{post_id}'
        return await self._request_json('GET', url)


    async def create_post(self, payload: dict) -> dict:
        url = f'{self.base_url}/posts'
        return await self._request_json(
            'POST',
            url,
            json=payload
        )


    async def get_posts_concurrently(
            self,
            post_ids: list[int],
    ) -> list[dict]:

        tasks = [
            self.get_post(post_id)
            for post_id in post_ids
        ]

        return list(
            await asyncio.gather(*tasks)
        )


    async def timeout_demo(
            self,
            delay_seconds: float,
            timeout_seconds: float
    ) -> dict:

        url = f'{self.delay_base_url}/delay/{delay_seconds}'

        try:
            response = await self.client.get(
                url,
                timeout=timeout_seconds
            )

            response.raise_for_status()

            return {
                'delay_seconds': delay_seconds,
                'timeout_seconds': timeout_seconds,
                'message': '외부 API 호출 제한 시간 안에 완료되엇습니다.'
            }

        except httpx.TimeoutException as error:
            raise ExternalApiTimeoutError(
                '외부 API 응답 시간이 초과되었습니다.'
            ) from error

        except httpx.HTTPStatusError as error:
            raise ExternalApiStatusError(
                status_code=error.response.status_code,
                message='외부 API가 오류 상태 코드를 반환했습니다.'
            ) from error

        except httpx.RequestError as error:
            raise ExternalApiConnectionError(
                '외부 API에 연결할 수 없습니다.'
            ) from error

