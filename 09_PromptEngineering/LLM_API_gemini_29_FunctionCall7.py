import os
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY를 읽을 수 없습니다.")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.7-flash"

def print_title(title:str):
    print('\n' + '-' * 80)
    print(title)
    print('-' * 80)
    print()


GEOCODING_URL = 'https://geocoding-api.open-meteo.com/v1/search'
WEATHER_URL = 'https://api.open-meteo.com/v1/forecast'
AIR_QUALITY_URL = 'https://air-quality-api.open-meteo.com/v1/air-quality'

REQUEST_TIMEOUT = 5
MAX_HTTP_ATTEMPTS = 3

class RetryaleApiError(RuntimeError):
    '''일시적 외부 API 오류'''
    pass

class PermanetApiError(RuntimeError):
    '''같은 요청을 반복해도 해결되지 않은 오류'''
    pass


WMO_WEATHER_MAP = {
    0: "맑음",

    1: "대체로 맑음",
    2: "부분적으로 흐림",
    3: "흐림",

    45: "안개",
    48: "서리성 안개",

    51: "약한 이슬비",
    53: "보통 이슬비",
    55: "강한 이슬비",

    56: "약한 어는 이슬비",
    57: "강한 어는 이슬비",

    61: "약한 비",
    63: "보통 비",
    65: "강한 비",

    66: "약한 어는 비",
    67: "강한 어는 비",

    71: "약한 눈",
    73: "보통 눈",
    75: "강한 눈",

    77: "싸락눈",

    80: "약한 소나기",
    81: "보통 소나기",
    82: "강한 소나기",

    85: "약한 눈 소나기",
    86: "강한 눈 소나기",

    95: "뇌우",
    96: "약한 우박을 동반한 뇌우",
    99: "강한 우박을 동반한 뇌우",
}

def weather_code_text(
        weather_code
) -> str:

    try:
        code = int(weather_code)
    except (TypeError, ValueError):
        return '알수 없음'

    return (
        WMO_WEATHER_MAP.get(code, f'알 수 없는 코드({code})')
    )


def us_aqi_to_text(value) -> str:

    if value is None:
        return '알 수 없음'

    try:
        aqi = float(value)
    except (TypeError, ValueError):
        return '알 수 없음'

    if aqi <= 50:
        return '좋음'

    if aqi <= 100:
            return '보통'

    if aqi <= 150:
            return '민감군에 나쁨'

    if aqi <= 200:
            return '나쁨'

    if aqi <= 250:
            return '매우 나쁨'

    return '위험'


def request_json(
    url: str,
    params: dict,
    max_attempts: int = MAX_HTTP_ATTEMPTS
) -> dict:


    for attempt in range(1, max_attempts + 1):
        print('\n[HTTP Request]')
        print(f'attempt: {attempt}/{max_attempts}')
        print(f'url: {url}')
        print(f'params: {json.dumps(params, ensure_ascii=False)}')

        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            print(f'status code: {response.status_code}')

            if response.status_code == 429 or 500 <= response.status_code <= 599:
                raise RetryaleApiError(
                        '외부 API가 일시적으로 요청 처리를 하지 못했습니다. '
                        f'HTTP {response.status_code}'
                )

            if 400 <= response.status_code <= 499:
                try:
                        error_body = response.json()
                except ValueError:
                        error_body = {
                            'raw_text': response.text[:500]
                        }

                raise PermanetApiError(
                        '외부 API 요청이 거부되었습니다. '
                        f'HTTP {response.status_code}, body={error_body}'
                )

            response.raise_for_status()

            try:
                return response.json()
            except ValueError as error:
                raise PermanetApiError(
                    '외부 API 응답을 JSON으로 해석 할 수 없습니다.'
                ) from error

        except requests.Timeout:
            print('Timeout 발생')

            if attempt >= max_attempts:
                raise RetryaleApiError(
                    '외부 API 요청 시간이 초과 되었습니다'
                )


        wait_seconds = min(2 ** (attempt - 1), 4)

        time.sleep(wait_seconds)

    raise RetryaleApiError(
        '외부 API 요청에 실패했습니다.'
    )


def geocode_city(
    city: str
) -> dict:
    data = request_json(
        url=GEOCODING_URL,
        params={
            'name': city,
            'count': 1,
            'language': 'ko',
            'format': 'json'
        }
    )

    results = data.get('results') or []

    if not results:

        return {
            'success': False,
            'error': {
                'code': 'location_not_found',
                'message': '도시를 찾을 수 없습니다.',
                'retryable': False
            },
            'query': city
        }

    first = results[0]

    return {
        'success': True,
        'data': {
            'name': first.get('name'),
            'country': first.get('country'),
            'admin1': first.get('admin1'),
            'latitude': first.get('latitude'),
            'longitude': first.get('longitude'),
            'timezone': first.get('timezone'),
        }
    }



        

             
    



