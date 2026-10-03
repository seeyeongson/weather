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

# WMO 날씨 코드 -> 한글 설명
WEATHER_CODES = {
    0: "맑음", 1: "대체로 맑음", 2: "주로 맑음", 3: "흐림",
    45: "안개", 48: "서리 안개",
    51: "약한 이슬비", 53: "이슬비", 55: "강한 이슬비",
    56: "약한 얼어붙는 이슬비", 57: "강한 얼어붙는 이슬비",
    61: "약한 비", 63: "비", 65: "강한 비",
    66: "약한 얼어붙는 비", 67: "강한 얼어붙는 비",
    71: "약한 눈", 73: "눈", 75: "강한 눈", 77: "싸락눈",
    80: "약한 소나기", 81: "소나기", 82: "강한 소나기",
    85: "약한 소낙눈", 86: "강한 소낙눈",
    95: "뇌우", 96: "우박 동반 뇌우", 99: "강한 우박 동반 뇌우",
}


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


# ---------------------------------------------------------------- 데이터 가공
def build_report(city: str, lat: float, lon: float, raw: dict) -> dict:
    """API 원본 데이터를 (날짜 -> 시각별 정보) 구조로 가공한다."""
    hourly, daily = raw["hourly"], raw["daily"]
    days = []
    for d_idx, date_str in enumerate(daily["time"]):
        entries = []
        for hour in TARGET_HOURS:
            key = f"{date_str}T{hour:02d}:00"
            i = hourly["time"].index(key)
            entries.append({
                "시각": f"{hour:02d}:00",
                "날씨": WEATHER_CODES.get(hourly["weather_code"][i], "알 수 없음"),
                "기온": round(hourly["temperature_2m"][i]),
                "강수확률": hourly["precipitation_probability"][i],
                "습도": hourly["relative_humidity_2m"][i],
                "풍속": round(hourly["wind_speed_10m"][i]),
            })
        days.append({
            "날짜": date_str,
            "최저기온": round(daily["temperature_2m_min"][d_idx]),
            "최고기온": round(daily["temperature_2m_max"][d_idx]),
            "예보": entries,
        })
    return {"지역": city, "위도": lat, "경도": lon, "일별": days}


# ---------------------------------------------------------------- 출력
def print_report(report: dict) -> None:
    """가공된 예보를 화면에 보기 좋게 출력한다."""
    hours_txt = " / ".join(
        f"{'오전' if h < 12 else '오후'} {h if h <= 12 else h - 12} 시"
        for h in TARGET_HOURS
    )
    print(f"\n{LINE_WIDE}")
    print(f"🌤️ {report['지역']} 날씨 예보 ({hours_txt} 기준)")
    print(LINE_WIDE)

    for idx, day in enumerate(report["일별"]):
        dt = datetime.strptime(day["날짜"], "%Y-%m-%d")
        label = DAY_LABELS[idx] if idx < len(DAY_LABELS) else f"{idx}일 후"
        print(f"\n📅 {label} ({dt.strftime('%m.%d.')})")
        print(LINE_THIN)
        for e in day["예보"]:
            hour = int(e["시각"][:2])
            icon = "🌅" if hour < 12 else "🌇"
            ampm = "오전" if hour < 12 else "오후"
            print(f"\n  {icon} {ampm} {e['시각']}")
            print(f"    날씨: {e['날씨']}")
            print(f"    기온: {e['기온']} °C")
            print(f"    강수확률: {e['강수확률']}%")
            print(f"    습도: {e['습도']}%")
            print(f"    풍속: {e['풍속']} m/s")
        print(f"\n  🌡️ 일일 기온: 최저 {day['최저기온']} °C / 최고 {day['최고기온']} °C")
        print(f"\n{LINE_WIDE}")


# ---------------------------------------------------------------- JSON 저장
def save_json(report: dict) -> str:
    """예보를 JSON 파일로 저장하고 파일명을 반환한다."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"weather_{report['지역']}_{stamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return filename


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
    report = build_report(place["name"], place["lat"], place["lon"], raw)
    print_report(report)

    answer = input("\n날씨 정보를 JSON 파일로 저장하시겠습니까? (y/n): ").strip().lower()
    if answer == "y":
        print(f"✅ 저장 완료: {save_json(report)}")


if __name__ == "__main__":
    main()
