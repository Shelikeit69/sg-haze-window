# sg-haze-window

**Live demo:** https://shelikeit69.github.io/sg-haze-window/

Haze Window estimates the next 24 hours of 1-hour PM2.5 for Singapore's five NEA regions during transboundary haze and suggests the daytime hour most likely to be cleanest for outdoor exercise. Entry to the AI4Climate 2026 Global Youth Climate Solutions Challenge (open track).

## Submission documents

| Document | File |
|---|---|
| Project statement | [docs/01_project_statement.md](docs/01_project_statement.md) |
| Data and AI statement | [docs/02_data_ai_statement.md](docs/02_data_ai_statement.md) |
| Validation plan | [docs/03_validation_plan.md](docs/03_validation_plan.md) |
| Demo video script | [docs/04_video_script.md](docs/04_video_script.md) |
| Shadow model promotion criteria | [docs/promotion_criteria.md](docs/promotion_criteria.md) |

## Results in one table

Test period 6 to 15 October 2026; method chosen on 26 September to 5 October 2026.

| | Average miss, µg/m³ | NEA band correct |
|---|---|---|
| Advice method (0.5 × current reading + 0.5 × rescaled CAMS) | 21.1 | 81 % |
| Repeat the current reading | 24.4 | 73 % |
| Machine-learning model, 13 to 24 h ahead (vs 31.9 for repeating the reading) | 36.4 | |

The machine-learning model did not beat the simple baseline and runs in shadow mode only. Results that use CAMS may be optimistic because we could not confirm when historical CAMS values were issued. Details and caveats: [docs/02_data_ai_statement.md](docs/02_data_ai_statement.md).

## Reproduce

```bash
pip install pandas numpy scikit-learn joblib
# keys for FIRMS (and OpenAQ, optional) are read from the environment
export FIRMS_MAP_KEY=...            # free from firms.modaps.eosdis.nasa.gov/api/map_key
python src/fetch_pm25.py 2026-08-01 2026-10-15          # repeat for 2023-2025 seasons
python src/fetch_weather.py 2026-08-01 2026-10-17
python src/fetch_upstream.py 2026-08-01 2026-10-15 --firms-only
python src/build_pm25_table.py && python src/fire_features.py
python src/window_eval.py          # model and baseline comparison
python src/advisor_eval.py         # advice method: validate, then test once
python src/export_app_data.py && python src/build_site.py   # demo data and GitHub Pages copy
python src/shadow.py predict && python src/shadow.py score  # daily shadow run
```

## API keys

No key is stored in this repository. The daily run reads the FIRMS key from a GitHub repository secret.

| Key | Used for | Where to find it again | Where it is stored |
|---|---|---|---|
| NASA FIRMS map key | Daily shadow run (fire detections) | Search the inbox of the registering email for "NASA FIRMS: Map key" from noreply@nasa.gov, or request one at https://firms.modaps.eosdis.nasa.gov/api/map_key/ | GitHub: Settings > Secrets and variables > Actions > `FIRMS_MAP_KEY` |
| OpenAQ API key | One-off check of upstream sensors (not used daily) | Log in at https://explore.openaq.org/account, section "API Key" | Not stored |

GitHub does not show a secret's value after it is saved. To change the FIRMS key, open the secret and paste the new value; the next daily run uses it.

## Daily shadow run

`.github/workflows/shadow-daily.yml` runs every day at 05:50 Singapore time. It logs the frozen model's forecast, scores earlier forecasts, refreshes the demo data and commits the results. To run it by hand: Actions > Daily shadow run > Run workflow. If the FIRMS secret is missing, the run stops at "Log today's shadow forecast" with a message saying so.

## Repository layout

```
data/raw/        source data as downloaded, never edited (FIRMS raw files are git-ignored)
data/processed/  cleaned tables built by src/
src/             data pipeline, features, evaluation, shadow model, site build
results/         metrics and test predictions written by src/
models/          frozen shadow model and its metadata
logs/            shadow model predictions, logged before outcomes are known
app/             demo page source (Claude artifact) and its data
web/             standalone GitHub Pages copy built from app/
docs/            competition documents
archive/         superseded downloads kept for reference
```

## License

MIT
