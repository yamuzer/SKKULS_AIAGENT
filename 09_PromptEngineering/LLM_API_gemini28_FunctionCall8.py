import json
import os
import time
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
)



# =========================================================
# 1. 기본 설정
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(
    dotenv_path=ENV_PATH
)

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY를 읽을 수 없습니다."
    )


client = genai.Client(
    api_key=api_key
)


MODEL_NAME = "gemini-3.7-flash"


# =========================================================
# 2. 외부 API Endpoint
# =========================================================

GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/"
    "v1/search"
)

WEATHER_URL = (
    "https://api.open-meteo.com/"
    "v1/forecast"
)

AIR_QUALITY_URL = (
    "https://air-quality-api.open-meteo.com/"
    "v1/air-quality"
)


# =========================================================
# 3. HTTP 정책
# =========================================================

REQUEST_TIMEOUT = 5

MAX_HTTP_ATTEMPTS = 3


# =========================================================
# 4. HTTP Custom Exception
# =========================================================

class RetryableApiError(
    RuntimeError
):
    """일시적 외부 API 오류"""
    pass


class PermanentApiError(
    RuntimeError
):
    """같은 요청을 반복해도 해결되지 않는 오류"""
    pass


# =========================================================
# 5. Weather Code → 한국어
# =========================================================

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


def weather_code_to_text(
    weather_code,
) -> str:

    try:

        code = int(
            weather_code
        )

    except (
        TypeError,
        ValueError,
    ):

        return "알 수 없음"


    return (
        WMO_WEATHER_MAP.get(
            code,
            f"알 수 없는 코드({code})",
        )
    )


# =========================================================
# 6. U.S. AQI → 한국어
# =========================================================

def us_aqi_to_text(
    value,
) -> str:

    if value is None:
        return "알 수 없음"


    try:

        aqi = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return "알 수 없음"


    if aqi <= 50:
        return "좋음"

    if aqi <= 100:
        return "보통"

    if aqi <= 150:
        return "민감군에 나쁨"

    if aqi <= 200:
        return "나쁨"

    if aqi <= 300:
        return "매우 나쁨"

    return "위험"


# =========================================================
# 7. 공통 HTTP JSON 요청
#
# Retry:
#
# - Timeout
# - ConnectionError
# - HTTP 429
# - HTTP 5xx
#
# Retry X:
#
# - HTTP 4xx
# - JSON Parsing Error
# =========================================================

def request_json(
    url: str,
    params: dict,
    max_attempts: int = MAX_HTTP_ATTEMPTS,
) -> dict:

    for attempt in range(
        1,
        max_attempts + 1,
    ):

        print(
            "\n[HTTP Request]"
        )

        print(
            "attempt:",
            f"{attempt}/{max_attempts}",
        )

        print(
            "url:",
            url,
        )

        print(
            "params:",
            json.dumps(
                params,
                ensure_ascii=False,
            ),
        )


        try:

            response = requests.get(

                url,

                params=params,

                timeout=REQUEST_TIMEOUT,
            )


            print(
                "status_code:",
                response.status_code,
            )


            # ---------------------------------------------
            # Retry 가능한 HTTP 오류
            # ---------------------------------------------

            if (
                response.status_code == 429
                or
                500 <= response.status_code <= 599
            ):

                raise RetryableApiError(
                    "외부 API가 일시적으로 "
                    "요청을 처리하지 못했습니다. "
                    f"HTTP {response.status_code}"
                )


            # ---------------------------------------------
            # Retry하면 안 되는 4xx
            # ---------------------------------------------

            if (
                400 <= response.status_code <= 499
            ):

                try:

                    error_body = (
                        response.json()
                    )

                except ValueError:

                    error_body = {
                        "raw_text":
                            response.text[:500]
                    }


                raise PermanentApiError(
                    "외부 API 요청이 거부되었습니다. "
                    f"HTTP {response.status_code}, "
                    f"body={error_body}"
                )


            response.raise_for_status()


            try:

                return response.json()


            except ValueError as error:

                raise PermanentApiError(
                    "외부 API 응답을 JSON으로 "
                    "해석할 수 없습니다."
                ) from error


        except requests.Timeout:

            print(
                "Timeout 발생"
            )


            if attempt >= max_attempts:

                raise RetryableApiError(
                    "외부 API 요청 시간이 "
                    "초과되었습니다."
                )


        except requests.ConnectionError:

            print(
                "ConnectionError 발생"
            )


            if attempt >= max_attempts:

                raise RetryableApiError(
                    "외부 API에 연결할 수 없습니다."
                )


        except RetryableApiError:

            if attempt >= max_attempts:
                raise


        # ---------------------------------------------
        # Exponential Backoff
        #
        # 1초 → 2초 → 최대 4초
        # ---------------------------------------------

        wait_seconds = min(
            2 ** (
                attempt - 1
            ),
            4,
        )


        print(
            "재시도 전 대기:",
            f"{wait_seconds}초",
        )


        time.sleep(
            wait_seconds
        )


    raise RetryableApiError(
        "외부 API 요청에 실패했습니다."
    )


# =========================================================
# 8. 도시 → 위도 / 경도
# =========================================================

def geocode_city(
    city: str,
) -> dict:

    data = request_json(

        url=GEOCODING_URL,

        params={
            "name":
                city,

            "count":
                1,

            "language":
                "ko",

            "format":
                "json",
        },
    )


    results = (
        data.get(
            "results"
        )
        or []
    )


    if not results:

        return {
            "success":
                False,

            "error": {
                "code":
                    "location_not_found",

                "message":
                    "도시를 찾을 수 없습니다.",

                "retryable":
                    False,
            },

            "query":
                city,
        }


    first = results[0]


    return {
        "success":
            True,

        "data": {
            "name":
                first.get(
                    "name"
                ),

            "country":
                first.get(
                    "country"
                ),

            "admin1":
                first.get(
                    "admin1"
                ),

            "latitude":
                first.get(
                    "latitude"
                ),

            "longitude":
                first.get(
                    "longitude"
                ),

            "timezone":
                first.get(
                    "timezone"
                ),
        },
    }


# =========================================================
# 9. Function A
# 현재 날씨 조회
# =========================================================

def get_current_weather(
    city: str,
) -> dict:

    city = city.strip()


    try:

        location_result = (
            geocode_city(
                city
            )
        )


        if not location_result[
            "success"
        ]:

            return (
                location_result
            )


        location = (
            location_result[
                "data"
            ]
        )


        data = request_json(

            url=WEATHER_URL,

            params={
                "latitude":
                    location[
                        "latitude"
                    ],

                "longitude":
                    location[
                        "longitude"
                    ],

                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),

                "timezone":
                    "auto",
            },
        )


        current = (
            data.get(
                "current"
            )
        )


        units = (
            data.get(
                "current_units"
            )
            or {}
        )


        if not current:

            return {
                "success":
                    False,

                "error": {
                    "code":
                        "weather_data_missing",

                    "message":
                        "현재 날씨 데이터가 없습니다.",

                    "retryable":
                        False,
                },
            }


        weather_code = (
            current.get(
                "weather_code"
            )
        )


        return {
            "success":
                True,

            "source":
                "Open-Meteo Weather",

            "location":
                location,

            "weather": {
                "time":
                    current.get(
                        "time"
                    ),

                "temperature":
                    current.get(
                        "temperature_2m"
                    ),

                "temperature_unit":
                    units.get(
                        "temperature_2m"
                    ),

                "apparent_temperature":
                    current.get(
                        "apparent_temperature"
                    ),

                "apparent_temperature_unit":
                    units.get(
                        "apparent_temperature"
                    ),

                "relative_humidity":
                    current.get(
                        "relative_humidity_2m"
                    ),

                "humidity_unit":
                    units.get(
                        "relative_humidity_2m"
                    ),

                "precipitation":
                    current.get(
                        "precipitation"
                    ),

                "precipitation_unit":
                    units.get(
                        "precipitation"
                    ),

                "weather_code":
                    weather_code,

                "weather_description":
                    weather_code_to_text(
                        weather_code
                    ),

                "wind_speed":
                    current.get(
                        "wind_speed_10m"
                    ),

                "wind_speed_unit":
                    units.get(
                        "wind_speed_10m"
                    ),
            },
        }


    except RetryableApiError as error:

        return {
            "success":
                False,

            "error": {
                "code":
                    "weather_temporary_error",

                "message":
                    str(
                        error
                    ),

                "retryable":
                    True,
            },
        }


    except PermanentApiError as error:

        return {
            "success":
                False,

            "error": {
                "code":
                    "weather_api_error",

                "message":
                    str(
                        error
                    ),

                "retryable":
                    False,
            },
        }


# =========================================================
# 10. Function B
# 현재 공기질 조회
# =========================================================

def get_current_air_quality(
    city: str,
) -> dict:

    city = city.strip()


    try:

        location_result = (
            geocode_city(
                city
            )
        )


        if not location_result[
            "success"
        ]:

            return (
                location_result
            )


        location = (
            location_result[
                "data"
            ]
        )


        data = request_json(

            url=AIR_QUALITY_URL,

            params={
                "latitude":
                    location[
                        "latitude"
                    ],

                "longitude":
                    location[
                        "longitude"
                    ],

                "current": (
                    "pm10,"
                    "pm2_5,"
                    "us_aqi,"
                    "european_aqi"
                ),

                "timezone":
                    "auto",
            },
        )


        current = (
            data.get(
                "current"
            )
        )


        units = (
            data.get(
                "current_units"
            )
            or {}
        )


        if not current:

            return {
                "success":
                    False,

                "error": {
                    "code":
                        "air_quality_data_missing",

                    "message":
                        "현재 공기질 데이터가 없습니다.",

                    "retryable":
                        False,
                },
            }


        us_aqi = (
            current.get(
                "us_aqi"
            )
        )


        return {
            "success":
                True,

            "source":
                "Open-Meteo Air Quality",

            "location":
                location,

            "air_quality": {
                "time":
                    current.get(
                        "time"
                    ),

                "pm2_5":
                    current.get(
                        "pm2_5"
                    ),

                "pm2_5_unit":
                    units.get(
                        "pm2_5"
                    ),

                "pm10":
                    current.get(
                        "pm10"
                    ),

                "pm10_unit":
                    units.get(
                        "pm10"
                    ),

                "us_aqi":
                    us_aqi,

                "us_aqi_category":
                    us_aqi_to_text(
                        us_aqi
                    ),

                "european_aqi":
                    current.get(
                        "european_aqi"
                    ),
            },
        }


    except RetryableApiError as error:

        return {
            "success":
                False,

            "error": {
                "code":
                    "air_quality_temporary_error",

                "message":
                    str(
                        error
                    ),

                "retryable":
                    True,
            },
        }


    except PermanentApiError as error:

        return {
            "success":
                False,

            "error": {
                "code":
                    "air_quality_api_error",

                "message":
                    str(
                        error
                    ),

                "retryable":
                    False,
            },
        }


# =========================================================
# 11. Function C
# 야외활동 적합성 평가
#
# Weather Result ─────┐
#                    ├─→ evaluate_outdoor_activity
# Air Result ─────────┘
#
# =========================================================

def evaluate_outdoor_activity(
    temperature: float,
    apparent_temperature: float,
    precipitation: float,
    wind_speed: float,
    weather_description: str,
    us_aqi: float,
) -> dict:

    score = 100

    reasons = []

    warnings = []


    # =====================================================
    # A. 강수
    # =====================================================

    if precipitation >= 1.0:

        score -= 40

        reasons.append(
            "현재 강수가 뚜렷합니다."
        )


    elif precipitation > 0:

        score -= 20

        reasons.append(
            "현재 약한 강수가 있습니다."
        )


    else:

        reasons.append(
            "현재 강수량은 0에 가깝습니다."
        )


    # =====================================================
    # B. 체감온도
    # =====================================================

    if (
        apparent_temperature >= 35
        or
        apparent_temperature <= -5
    ):

        score -= 35

        reasons.append(
            "체감온도가 야외활동에 "
            "부담이 큰 수준입니다."
        )


    elif (
        apparent_temperature >= 30
        or
        apparent_temperature <= 0
    ):

        score -= 15

        reasons.append(
            "체감온도에 주의가 필요합니다."
        )


    else:

        reasons.append(
            "체감온도는 비교적 무난한 범위입니다."
        )


    # =====================================================
    # C. 풍속
    # =====================================================

    if wind_speed >= 35:

        score -= 30

        reasons.append(
            "바람이 강합니다."
        )


    elif wind_speed >= 20:

        score -= 10

        reasons.append(
            "바람이 다소 강합니다."
        )


    else:

        reasons.append(
            "풍속은 큰 부담이 없는 수준입니다."
        )


    # =====================================================
    # D. U.S. AQI
    # =====================================================

    if us_aqi >= 151:

        score -= 45

        reasons.append(
            "공기질이 나쁩니다."
        )

        warnings.append(
            "장시간 야외활동을 피하는 것이 좋습니다."
        )


    elif us_aqi >= 101:

        score -= 25

        reasons.append(
            "민감군은 공기질에 주의가 필요합니다."
        )

        warnings.append(
            "호흡기 민감군은 활동 강도를 줄이세요."
        )


    elif us_aqi >= 51:

        score -= 10

        reasons.append(
            "공기질은 보통 수준입니다."
        )


    else:

        reasons.append(
            "공기질은 좋은 수준입니다."
        )


    # =====================================================
    # E. 최종 Score 범위
    # =====================================================

    score = max(
        0,
        min(
            100,
            score,
        ),
    )


    # =====================================================
    # F. 등급
    # =====================================================

    if score >= 80:

        decision = (
            "좋음"
        )

        recommendation = (
            "일반적인 야외활동을 하기 좋은 조건입니다."
        )


    elif score >= 55:

        decision = (
            "주의"
        )

        recommendation = (
            "야외활동은 가능하지만 "
            "기상 또는 공기질 조건을 고려해 "
            "활동 강도와 시간을 조절하세요."
        )


    else:

        decision = (
            "비추천"
        )

        recommendation = (
            "현재는 장시간 또는 강도 높은 "
            "야외활동을 권장하기 어렵습니다."
        )


    # =====================================================
    # G. Result
    # =====================================================

    return {
        "success":
            True,

        "decision":
            decision,

        "score":
            score,

        "recommendation":
            recommendation,

        "input_conditions": {
            "temperature":
                temperature,

            "apparent_temperature":
                apparent_temperature,

            "precipitation":
                precipitation,

            "wind_speed":
                wind_speed,

            "weather_description":
                weather_description,

            "us_aqi":
                us_aqi,

            "us_aqi_category":
                us_aqi_to_text(
                    us_aqi
                ),
        },

        "reasons":
            reasons,

        "warnings":
            warnings,
    }


# =========================================================
# 12. Function Registry
# =========================================================

FUNCTION_MAP = {

    "get_current_weather":
        get_current_weather,

    "get_current_air_quality":
        get_current_air_quality,

    "evaluate_outdoor_activity":
        evaluate_outdoor_activity,
}


# =========================================================
# 13. Function Declaration A
# =========================================================

get_current_weather_tool = {
    'type': 'function',
    'name': 'get_current_weather',
    'description': (
        '도시의 현재 실제 날씨를 조회합니다. '
        '기온, 체감온도, 강수량, 날씨 상태, '
        '풍속 등이 필요할 때 사용합니다.'
    ),
    'parameters': {
        'type': 'object',
        'properties': {
            'city': {
                'type': 'string',
                'description': '날씨를 조회할 도시명'
            }
        },
        'required':[
            'city'
        ]
    }
}

# =========================================================
# 14. Function Declaration B
# =========================================================

get_current_air_quality_tool = {
    'type': 'function',
    'name': 'get_current_air_quality',
    'description': (
        '도시의 현재 실제 공기질을 조회합니다. '
        'PM2.5, PM10, U.S AQI 등이 필요할 때 사용합니다.'
    ),
    'parameters': {
        'type': 'object',
        'properties': {
            'city': {
                'type': 'string',
                'description': '공기질을 조회할 도시명'
            }
        },
        'required':[
            'city'
        ]
    }
}


# =========================================================
# 15. Function Declaration C
#
# 중요한 설명:
#
# 이 Function은 Weather/Air Result를 받은 후에만
# 호출하도록 description에 명시합니다.
# =========================================================

evaluate_outdoor_activity_tool = {
    'type': 'function',
    'name': 'evaluate_outdoor_activity',
    'description': (
        '실제 날씨 조회와 실제 공기질 조회가 모두 완료된 뒤 야외활동 적합성을 평가합니다. '
        'temperature, apparent_temperature, precipitation, wind_speed, weather_description은 '
        'get_current_weather Result의 실제 값을 사용하고, '
        'us_aqi는 get_current_air_quality Result의 실제 값을 사용해야 합니다. '
        '값을 추측해서 호출하면 안 됩니다.'
    ),
    'parameters': {
        'type': 'object',
        'properties': {
            'temperature': {
                'type': 'number',
                'description': 'Weather Result의 실제 현재 기온'
            },
            'apparent_temperature': {
                'type': 'number',
                'description': 'Weather Result의 실제 체감온도'
            },
            'precipitation': {
                'type': 'number',
                'description': 'Weather Result의 실제 현재 강수량'
            },
            'wind_speed': {
                'type': 'number',
                'description': 'Weather Result의 실제 현재 10m 풍속'
            },
            'weather_description': {
                'type': 'string',
                'description': 'Weather Result의 실제 날씨 설명'
            },
            'us_aqi': {
                'type': 'number',
                'description': 'Air Quality Result의 실제 U.S. AQI'
            },
        },
        'required':[
            'temperature',
            'apparent_temperature',
            'precipitation',
            'wind_speed',
            'weather_description',
            'us_aqi'
        ]
    }
}




TOOLS = [
    get_current_weather_tool,
    get_current_air_quality_tool,
    evaluate_outdoor_activity_tool,
]


# =========================================================
# 16. System Instruction
# =========================================================




# =========================================================
# 17. Pydantic Arguments
# =========================================================

class CityArguments(
    BaseModel
):

    model_config = (
        ConfigDict(
            strict=True,
            extra="forbid",
        )
    )

    city: str = Field(
        min_length=1,
        max_length=100,
    )


class OutdoorActivityArguments(
    BaseModel
):

    # 숫자가 int 또는 float로 올 수 있으므로
    # 이번 Model은 strict=True를 사용하지 않습니다.

    model_config = (
        ConfigDict(
            extra="forbid",
        )
    )

    temperature: float

    apparent_temperature: float

    precipitation: float = Field(
        ge=0,
    )

    wind_speed: float = Field(
        ge=0,
    )

    weather_description: str = Field(
        min_length=1,
    )

    us_aqi: float = Field(
        ge=0,
    )


ARGUMENT_MODEL_MAP = {

    "get_current_weather":
        CityArguments,

    "get_current_air_quality":
        CityArguments,

    "evaluate_outdoor_activity":
        OutdoorActivityArguments,
}


# =========================================================
# 18. Argument Validation
# =========================================================

def validate_arguments(
    function_name: str,
    arguments,
) -> dict:

    model_class = (
        ARGUMENT_MODEL_MAP.get(
            function_name
        )
    )


    if model_class is None:

        return {
            "valid":
                False,

            "data":
                None,

            "errors": [
                {
                    "message":
                        "등록되지 않은 Function입니다."
                }
            ],
        }


    if not isinstance(
        arguments,
        dict,
    ):

        return {
            "valid":
                False,

            "data":
                None,

            "errors": [
                {
                    "message":
                        "arguments는 dict여야 합니다."
                }
            ],
        }


    try:

        validated = (
            model_class
            .model_validate(
                arguments
            )
        )


        return {
            "valid":
                True,

            "data":
                validated
                .model_dump(),

            "errors":
                [],
        }


    except ValidationError as error:

        return {
            "valid":
                False,

            "data":
                None,

            "errors":
                error.errors(),
        }


# =========================================================
# 19. Function Call 하나 실행
# =========================================================

def execute_call(
    call,
) -> dict:

    started_at = (
        time.perf_counter()
    )


    validation = (
        validate_arguments(

            function_name=(
                call.name
            ),

            arguments=(
                call.arguments
            ),
        )
    )


    if not validation[
        "valid"
    ]:

        result = {
            "success":
                False,

            "error": {
                "code":
                    "argument_validation_error",

                "message":
                    "Function Arguments 검증 실패",

                "details":
                    validation[
                        "errors"
                    ],

                "retryable":
                    False,
            },
        }


    else:

        python_function = (
            FUNCTION_MAP.get(
                call.name
            )
        )


        if python_function is None:

            result = {
                "success":
                    False,

                "error": {
                    "code":
                        "function_not_registered",

                    "message":
                        "실행할 Function을 찾을 수 없습니다.",

                    "retryable":
                        False,
                },
            }


        else:

            try:

                result = (
                    python_function(
                        **validation[
                            "data"
                        ]
                    )
                )


            except Exception as error:

                result = {
                    "success":
                        False,

                    "error": {
                        "code":
                            "unexpected_function_error",

                        "message":
                            str(
                                error
                            ),

                        "error_type":
                            type(
                                error
                            ).__name__,

                        "retryable":
                            False,
                    },
                }


    elapsed_seconds = (
        time.perf_counter()
        - started_at
    )


    return {
        "call":
            call,

        "function_name":
            call.name,

        "elapsed_seconds":
            round(
                elapsed_seconds,
                3,
            ),

        "result":
            result,
    }


# =========================================================
# 20. Function Result 생성
# =========================================================

def build_function_result(
    call,
    result: dict,
) -> dict:

    return {

        "type":
            "function_result",

        "name":
            call.name,

        "call_id":
            call.id,

        "result": [
            {
                "type":
                    "text",

                "text":
                    json.dumps(
                        result,
                        ensure_ascii=False,
                    ),
            }
        ],
    }


# =========================================================
# 21. Function Call 추출
# =========================================================

def get_function_calls(
    interaction,
) -> list:

    return [

        step

        for step in (
            interaction.steps
            or []
        )

        if getattr(
            step,
            "type",
            None,
        )
        == "function_call"
    ]


# =========================================================
# 22. 현재 Round Function Call 출력
# =========================================================

def print_function_calls(
    function_calls: list,
):

    print(
        "Function Call 수:",
        len(
            function_calls
        ),
    )


    for index, call in enumerate(
        function_calls,
        start=1,
    ):

        print(
            "\n"
            + "-" * 80
        )

        print(
            f"Function Call #{index}"
        )

        print(
            "-" * 80
        )

        print(
            "call.id:",
            call.id,
        )

        print(
            "call.name:",
            call.name,
        )

        print(
            "call.arguments:",
            call.arguments,
        )


# =========================================================
# 23. 첫 단계 Parallel 실행
#
# Weather / Air Quality Function이
# 같은 Round에 여러 개 나오면
# ThreadPoolExecutor로 실제 병렬 실행
# =========================================================

def execute_calls_in_parallel(
    function_calls: list,
) -> list[dict]:

    max_workers = min(
        len(
            function_calls
        ),
        4,
    )


    print(
        "\n"
        + "=" * 90
    )

    print(
        "Application Parallel Execution"
    )

    print(
        "=" * 90
    )

    print(
        "Thread 수:",
        max_workers,
    )


    results = []


    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        future_map = {

            executor.submit(
                execute_call,
                call,
            ):
                call

            for call in (
                function_calls
            )
        }


        for future in as_completed(
            future_map
        ):

            item = (
                future.result()
            )


            print(
                "\n[병렬 실행 완료]"
            )

            print(
                "function:",
                item[
                    "function_name"
                ],
            )

            print(
                "call.id:",
                item[
                    "call"
                ].id,
            )

            print(
                "elapsed:",
                item[
                    "elapsed_seconds"
                ],
                "초",
            )

            print(
                json.dumps(
                    item[
                        "result"
                    ],
                    ensure_ascii=False,
                    indent=2,
                )
            )


            results.append(
                item
            )


    return results


# =========================================================
# 24. 현재 Round 실행 방법 결정
#
# 데이터 조회 Function이 2개 이상이면 병렬
#
# evaluator는 의존성이 있으므로
# 일반 순차 실행
# =========================================================

def execute_current_round(
    function_calls: list,
) -> list[dict]:

    data_function_names = {
        "get_current_weather",
        "get_current_air_quality",
    }


    all_are_data_functions = all(

        call.name
        in data_function_names

        for call
        in function_calls
    )


    if (
        len(
            function_calls
        )
        >= 2
        and
        all_are_data_functions
    ):

        return (
            execute_calls_in_parallel(
                function_calls
            )
        )


    # -----------------------------------------------------
    # Sequential 실행
    #
    # 대표적으로:
    # evaluate_outdoor_activity
    # -----------------------------------------------------

    results = []


    for call in (
        function_calls
    ):

        item = (
            execute_call(
                call
            )
        )


        print(
            "\n[Sequential Function 실행]"
        )

        print(
            "function:",
            item[
                "function_name"
            ],
        )

        print(
            "call.id:",
            call.id,
        )

        print(
            json.dumps(
                item[
                    "result"
                ],
                ensure_ascii=False,
                indent=2,
            )
        )


        results.append(
            item
        )


    return results


# =========================================================
# 25. End-to-End Mixed Workflow
#
# ROUND 1
#
# Weather + Air
# → Parallel
#
#
# ROUND 2
#
# evaluate_outdoor_activity
# → Sequential
#
#
# ROUND 3
#
# Function Call 없음
# → Final Answer
# =========================================================

def process_outdoor_question(
    question: str,
    max_rounds: int = 5,
) -> str:

    print(
        "\n"
        + "=" * 100
    )

    print(
        "사용자 질문"
    )

    print(
        "=" * 100
    )

    print(
        question
    )


    # =====================================================
    # 첫 Interaction
    #
    # auto:
    #
    # Tool이 필요하면 Function Call
    # 최종 단계에서는 자연어 답변 가능
    # =====================================================

    interaction = (
        client.interactions.create(

            model=MODEL_NAME,

            input=question,

            system_instruction=(
                SYSTEM_INSTRUCTION
            ),

            tools=TOOLS,

            generation_config={
                "tool_choice":
                    "auto",
            },
        )
    )


    # =====================================================
    # 여러 Round
    # =====================================================

    for round_number in range(
        1,
        max_rounds + 1,
    ):

        print(
            "\n"
            + "#" * 100
        )

        print(
            f"ROUND {round_number}"
        )

        print(
            "#" * 100
        )


        print(
            "interaction.id:",
            interaction.id,
        )


        function_calls = (
            get_function_calls(
                interaction
            )
        )


        print_function_calls(
            function_calls
        )


        # =================================================
        # 더 이상 Function Call이 없음
        # → 최종 답변
        # =================================================

        if not function_calls:

            final_text = (
                interaction.output_text
                or
                "최종 답변이 생성되지 않았습니다."
            )


            print(
                "\n"
                + "=" * 100
            )

            print(
                "Workflow 완료"
            )

            print(
                "=" * 100
            )

            print(
                final_text
            )


            return final_text


        # =================================================
        # Application 실행
        # =================================================

        executed_items = (
            execute_current_round(
                function_calls
            )
        )


        # =================================================
        # 모든 Call에 Result가 있는지 확인
        # =================================================

        if (
            len(
                executed_items
            )
            !=
            len(
                function_calls
            )
        ):

            raise RuntimeError(
                "Function Call 수와 "
                "실행 Result 수가 다릅니다."
            )


        # =================================================
        # Function Result 생성
        #
        # Parallel 완료 순서가 달라도
        # call_id가 있으므로 정확히 매핑됨
        # =================================================

        function_results = [

            build_function_result(

                call=item[
                    "call"
                ],

                result=item[
                    "result"
                ],
            )

            for item in (
                executed_items
            )
        ]


        print(
            "\n"
            + "=" * 90
        )

        print(
            "Function Result Mapping"
        )

        print(
            "=" * 90
        )


        for result_input in (
            function_results
        ):

            print(
                "name:",
                result_input[
                    "name"
                ],
                "| call_id:",
                result_input[
                    "call_id"
                ],
            )


        # =================================================
        # 다음 Interaction
        #
        # 여기서:
        #
        # ROUND 1 결과 뒤
        # → evaluator Call
        #
        # ROUND 2 결과 뒤
        # → 최종 Text
        #
        # 가 기대됨
        # =================================================

        interaction = (
            client.interactions.create(

                model=MODEL_NAME,

                previous_interaction_id=(
                    interaction.id
                ),

                input=(
                    function_results
                ),

                system_instruction=(
                    SYSTEM_INSTRUCTION
                ),

                tools=TOOLS,

                generation_config={
                    "tool_choice":
                        "auto",
                },
            )
        )


    raise RuntimeError(
        "Mixed Function Calling Workflow가 "
        f"{max_rounds} Round 안에 끝나지 않았습니다."
    )
