import os
import sys

import pandas as pd


COUNTRY_COORDS = {
    "United States": ("United States", (40.7128, -74.0060)),
    "USA": ("United States", (40.7128, -74.0060)),
    "China": ("China", (39.9042, 116.4074)),
    "中国": ("China", (39.9042, 116.4074)),
    "Canada": ("Canada", (45.4215, -75.6972)),
    "Brazil": ("Brazil", (-15.7975, -47.8919)),
    "Singapore": ("Singapore", (1.3521, 103.8198)),
    "Australia": ("Australia", (-35.2809, 149.1300)),
    "India": ("India", (28.6139, 77.2090)),
    "Japan": ("Japan", (35.6895, 139.6917)),
    "Hong Kong": ("Hong Kong", (22.3193, 114.1694)),
    "Not specified": ("Unknown", (0.0, 0.0)),
    "": ("Unknown", (0.0, 0.0)),
}


def normalize_country(country: str) -> tuple[str, float, float]:
    country = (country or "").strip()
    normalized, coords = COUNTRY_COORDS.get(country, ("Unknown", (0.0, 0.0)))
    lat, lon = coords
    return normalized, lat, lon


def main(users_csv: str, output_csv: str):
    try:
        df = pd.read_csv(users_csv)
    except FileNotFoundError:
        print(f"Файл с пользователями для Kibana не найден: {users_csv}")
        return
    except Exception as e:
        print(f"Ошибка при чтении {users_csv}: {e}")
        return

    if df.empty:
        print(f"Файл {users_csv} пуст, экспорт для Kibana пропущен")
        return

    norm_countries = []
    coords = []
    for _, row in df.iterrows():
        country = row.get("country", "")
        normalized, lat, lon = normalize_country(str(country))
        norm_countries.append(normalized)
        coords.append((lat, lon))

    df["country_normalized"] = [c for c, _ in zip(norm_countries, coords)]
    df["coordinates"] = [f"{lat},{lon}" for lat, lon in coords]
    df["lat"] = [lat for lat, _ in coords]
    df["lon"] = [lon for _, lon in coords]

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    try:
        df.to_csv(output_csv, index=False, encoding="utf-8")
        print(f"Kibana CSV сохранён в {output_csv}")
    except Exception as e:
        print(f"Ошибка при сохранении Kibana CSV: {e}")


if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            print("Usage: python kibana_export.py <users_csv> <output_csv>")
            raise SystemExit(0)
        main(sys.argv[1], sys.argv[2])
    except Exception as e:
        print(f"Unexpected error in kibana_export main(): {e}")


