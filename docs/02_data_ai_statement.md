# Data and AI statement

## Data

| Source | What we use | Period | Access |
|---|---|---|---|
| NEA via data.gov.sg (v2 real-time API) | 1-hour PM2.5, µg/m³, for the five NEA regions | 1 Aug to 15 Nov in 2023, 2024 and 2025; 1 Aug to 15 Oct 2026 | Open, no key |
| CAMS global atmospheric composition forecast, via Open-Meteo air-quality API | Forecast PM2.5 at the five NEA region points | Same periods, plus two days ahead for live use | Open, no key |
| Open-Meteo historical weather API | Wind speed and direction, rain, humidity, boundary layer height | Same periods | Open, no key |
| NASA FIRMS, VIIRS (Suomi NPP and NOAA-20) | Active fire detections over Sumatra, Kalimantan and Peninsular Malaysia | Standard processing to 30 Jun 2026, near-real-time after | Free key |
| OpenAQ v3 | Low-cost sensors in Palembang, Malacca and Johor | Checked, not used: Palembang had 65 hours and Malacca 97 hours of data in six weeks | Free key |

All NEA data covers 394 days. Inside those days 80 hours are missing at the source, mostly in 2023, and three days (8 October, 4 and 5 November 2023) return no data at all. Missing hours are left missing and never filled in.

Known problems with the data:

- The older data.gov.sg v1 endpoint leaves out the 00:00 reading each day. We use v2, which returns all 24 hours.
- The historical weather API returns model values for recent hours, including hours that had not happened when the file was downloaded. Model inputs only use weather at or before the forecast's issue time.
- We could not confirm whether historical CAMS values were issued before the hours they forecast. Test results that use CAMS may be better than live use.
- FIRMS standard and near-real-time products are processed differently, and 2026 (near-real-time) shows far more detections than 2023 to 2025. Part of this is a much worse fire season, but we cannot rule out a product difference.
- Cloud and smoke hide fires from the satellites, so fire counts are a lower bound.

## Methods and models

**Advice shown to users.** For each region and each hour h in the next 24, the estimate is 0.5 × the current NEA reading + 0.5 × CAMS(h) × k, where k is the median ratio of NEA readings to CAMS since 1 August of the current year. The suggested hour is the daytime hour (06:00 to 21:00) with the lowest CAMS forecast. Both weights were picked from five options on a validation period (26 September to 5 October 2026) and tested once on 6 to 15 October 2026.

**Machine-learning model (shadow mode).** scikit-learn HistGradientBoostingRegressor, version shadow-v1, frozen on 15 October 2026. It predicts the log change from the current reading for horizons of 1 to 24 hours. Inputs: recent NEA readings (lags, 24-hour mean and maximum, island mean and maximum), weather at issue time, hour of day, region, FIRMS fire counts and fire radiative power in three source regions over the previous 24 and 24 to 48 hours (counted three hours after the satellite pass to allow for publishing delay), and CAMS for the target hour. Separate quantile models give P10 and P90. It was trained on 1.1 million rows covering all four years.

**Baselines.** Repeating the current reading; the reading at the same hour yesterday; the median for that hour in the training data; raw CAMS.

## Results (test period 6 to 15 October 2026)

| | Average miss, µg/m³ | NEA band correct |
|---|---|---|
| Advice method | 21.1 | 81 % |
| Repeat current reading | 24.4 | 73 % |
| Scaled CAMS alone | 25.4 | |

Suggested hour versus a random daytime hour: 12.1 µg/m³ lower. A fixed morning hour did 13.1 on the test days but worse in validation. The machine-learning model did not beat repeating the current reading (36.4 against 31.9 µg/m³ at 13 to 24 hours ahead). Full results and the code that produced them are in the repository (`results/`, `src/`).

## Tools

Python (pandas, NumPy, scikit-learn), plain HTML and JavaScript for the demo, GitHub Pages for hosting. Claude (Anthropic) was used as a coding and writing assistant. No DeepSeek model is used in the solution.

## Responsible use

- The page shows the typical error from testing next to every estimate and tells people to check the live NEA reading before going out.
- The page quotes NEA's advice only where we could check the wording (Bands I and II) and points to haze.gov.sg for Bands III and IV.
- The machine-learning model cannot change the advice until it meets published criteria (`docs/promotion_criteria.md`).
- No personal data is collected. The page stores only the last region a visitor picked, in their own browser.
- API keys are kept outside the repository.
