from collections.abc import AsyncIterator

from google import genai
from google.genai import errors, types

from app.schemas.llm import ChatRequest


class GeminiConfigurationError(Exception):
    pass


class GeminiAPIError(Exception):

    def __init__(
            self,
            code: int | None,
            message: str
    ):
        self.code = code
        self.message = message

        super().__init__(
            f'Gemini API Error ({code}): {message}'
        )


class GeminiService:

    def __init__(
            self,
            api_key: str | None,
            model: str,
            default_temperature: float
    ):
        self.api_key = api_key.strip() if api_key else ''
        self.model = model
        self.default_temperature = default_temperature


    def ensure_configured(self) -> None:
        if not self.api_key:
            raise GeminiConfigurationError(
                'GEMINI_API_KEY가 설정되지 않았습니다.'
            )


    def _make_config(
            self,
            request: ChatRequest
    ) -> types.GenerateContentConfig:

        temperature = (
            request.temperature 
            if request.temperature is not None
            else self.default_temperature
        )

        return types.GenerateContentConfig(
            system_instruction=request.system_prompt,
            temperature=temperature
        )


    async def generate(
            self,
            request: ChatRequest
    ) -> str:

        self.ensure_configured()

        client = genai.Client(
            api_key=self.api_key
        )

        async_client = client.aio

        try:
            response = await async_client.models.generate_content(
                model=self.model,
                contents=request.message,
                config=self._make_config(request)
            )

            return response.text or ''

        except errors.APIError as error:
            raise GeminiAPIError(
                code=getattr(
                    error,
                    'code',
                    None
                ),
                message=getattr(
                    error,
                    'message',
                    str(error)
                )
            ) from error

        finally:
            await async_client.aclose()
            client.close()


    async def stream(
            self,
            request: ChatRequest
    ) -> AsyncIterator[str]:

        self.ensure_configured()

        client = genai.Client(
            api_key=self.api_key
        )

        async_client = client.aio

        try:
            stream = await async_client.models.generate_content_stream(
                model=self.model,
                contents=request.message,
                config=self._make_config(request)
            )

            async for chunck in stream:
                text = chunck.text

                if text:
                    yield text

        except errors.APIError as error:
            raise GeminiAPIError(
                code=getattr(
                    error,
                    'code',
                    None
                ),
                message=getattr(
                    error,
                    'message',
                    str(error)
                )
            ) from error

        finally:
            await async_client.aclose()
            client.close()




    