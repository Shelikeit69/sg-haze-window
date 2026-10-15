# Raw data

Files here are kept exactly as downloaded. Do not edit them; build cleaned tables in `data/processed/` with code in `src/`.

| Folder | Source | Script | Notes |
|---|---|---|---|
| `pm25/` | NEA via data.gov.sg v2 `real-time/api/pm25?date=` | `src/fetch_pm25.py` | 1-hour PM2.5, µg/m³, 5 regions. Official observations. |
| `weather/weather_*` | Open-Meteo archive API | `src/fetch_weather.py` | Wind, rain, humidity, boundary layer height at NEA region label points. |
| `weather/cams_*` | Open-Meteo air-quality API (CAMS) | `src/fetch_weather.py` | Modelled PM2.5. A model value, never treated as ground truth. |

## Known caveats

1. **v1 PM2.5 endpoint drops 00:00.** The v1 `environment/pm25?date=` call returns 23 hours per day and omits midnight. v2 returns all 24. v1 downloads are kept in `archive/raw_pm25_v1/` for reference only.
2. **Archive weather includes model values for recent hours.** The archive endpoint returns values up to the end of the requested day, including hours that had not yet happened at download time (`_pulled_at_utc` in each file). Recent values come from forecast models, not reanalysis. Model inputs must not use weather values from after the forecast issue time.
3. **CAMS history provenance not yet confirmed.** Whether the historical CAMS series is made of forecasts issued in advance (usable as a forecast input) or of later analyses (would leak information) still needs to be checked before CAMS is used in the backtest.
