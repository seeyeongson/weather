"""
날씨 예보 프로그램 (Open-Meteo API 사용)
- 사용자에게 지역을 입력받음 (기본값: 천안)
- 오늘, 내일, 모레까지 3일간의 날씨를 오전 6시, 오후 3시 기준으로 표시
- Open-Meteo API 사용 (인증키 불필요, 무료)

GitHub 프로젝트 주소: https://github.com/내아이디/python-weather-report
(↑ 본인의 실제 저장소 주소로 반드시 수정하세요)
"""

import json
import sys
from datetime import datetime
from typing import Optional

import requests

# ---------------------------------------------------------------- 설정
DEFAULT_CITY = "천안"          # 기본 지역
FORECAST_DAYS = 3              # 예보 일수 (2 이상 자유롭게 변경 가능)
TARGET_HOURS = (6, 15)         # 표시할 시각 (오전 6시, 오후 3시)
DAY_LABELS = ["오늘", "내일", "모레", "글피"]
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
LINE_WIDE = "=" * 70
LINE_THIN = "-" * 55

# ---------------------------------------------------------------- 지역 검색
def get_coordinates(city: str) -> Optional[dict]:
    """지역 이름으로 위도/경도를 조회한다. 실패하면 None."""
    params = {"name": city, "count": 1, "language": "ko", "format": "json"}
    res = requests.get(GEO_URL, params=params, timeout=10)
    results = res.json().get("results")
    if not results:
        return None
    r = results[0]
    return {"name": r.get("name", city), "lat": r["latitude"], "lon": r["longitude"]}


# ---------------------------------------------------------------- 날씨 조회
def get_weather(lat: float, lon: float) -> Optional[dict]:
    """위도/경도로 시간별·일별 예보 데이터를 가져온다."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relative_humidity_2m,"
                  "precipitation_probability,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "wind_speed_unit": "ms",
        "timezone": "Asia/Seoul",
        "forecast_days": FORECAST_DAYS,
    }
    res = requests.get(FORECAST_URL, params=params, timeout=10)
    return res.json()


# ---------------------------------------------------------------- 메인
def main() -> None:
    print("🌤️ 날씨 예보 프로그램 (Open-Meteo API)")
    print(LINE_THIN)
    print(f"오전 6 시, 오후 3 시 기준으로 {FORECAST_DAYS} 일간 날씨를 제공합니다.")
    print(LINE_THIN)

    city = input(f"\n날씨를 확인할 지역을 입력하세요 (기본값: {DEFAULT_CITY}): ").strip()
    city = city or DEFAULT_CITY

    place = get_coordinates(city)
    if place is None:
        print(f"❌ '{city}' 지역을 찾을 수 없습니다. 지역 이름을 확인해 주세요.")
        return

    print(f"\n📍 {place['name']} (위도: {place['lat']}, 경도: {place['lon']}) "
          f"의 날씨 정보를 가져옵니다...")

    raw = get_weather(place["lat"], place["lon"])
    print(f"✅ 시간별 데이터 {len(raw['hourly']['time'])}건 수신")


if __name__ == "__main__":
    main()
