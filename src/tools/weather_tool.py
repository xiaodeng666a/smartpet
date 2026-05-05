import json

import requests
from langchain.tools import tool


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


WEATHER_CODE_MAP = {
    0: "晴",
    1: "大致晴朗",
    2: "局部多云",
    3: "阴",
    45: "有雾",
    48: "有雾并伴随霜",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "较强毛毛雨",
    56: "冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "阵雨",
    82: "强阵雨",
    85: "小阵雪",
    86: "强阵雪",
    95: "雷暴",
    96: "伴有小冰雹的雷暴",
    99: "伴有大冰雹的雷暴",
}


def _weather_text(code: int | None) -> str:
    if code is None:
        return "未知天气"
    return WEATHER_CODE_MAP.get(code, f"天气代码 {code}")


def _geocode_city(city: str) -> dict | None:
    response = requests.get(
        GEOCODING_URL,
        params={"name": city, "count": 1, "language": "zh", "format": "json"},
        timeout=15,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    return results[0] if results else None


def _fetch_weather(latitude: float, longitude: float) -> dict:
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "forecast_days": 1,
            "models": "cma_grapes_global",
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def get_weather_payload(city: str) -> dict:
    cleaned = city.strip()
    if not cleaned:
        return {"ok": False, "message": "请告诉我你想查询哪个城市的天气。"}

    try:
        geo = _geocode_city(cleaned)
    except Exception as exc:
        return {"ok": False, "message": f"查询城市位置失败：{exc}"}

    if not geo:
        return {
            "ok": False,
            "message": f'我没有找到“{cleaned}”这个城市的位置，换一个更完整的地名试试吧。',
        }

    try:
        weather = _fetch_weather(geo["latitude"], geo["longitude"])
    except Exception as exc:
        return {"ok": False, "message": f"查询天气失败：{exc}"}

    current = weather.get("current", {})
    daily = weather.get("daily", {})
    max_temps = daily.get("temperature_2m_max") or []
    min_temps = daily.get("temperature_2m_min") or []
    daily_codes = daily.get("weather_code") or []

    resolved_name = geo.get("name", cleaned)
    admin1 = geo.get("admin1") or ""
    country = geo.get("country") or ""
    place = " ".join(part for part in [resolved_name, admin1, country] if part).strip()

    return {
        "ok": True,
        "city": cleaned,
        "resolved_place": place,
        "current_temperature_c": current.get("temperature_2m"),
        "current_weather_text": _weather_text(current.get("weather_code")),
        "today_weather_text": _weather_text(daily_codes[0] if daily_codes else None),
        "today_min_temperature_c": min_temps[0] if min_temps else None,
        "today_max_temperature_c": max_temps[0] if max_temps else None,
    }


@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city using Open-Meteo."""
    return json.dumps(get_weather_payload(city), ensure_ascii=False)
