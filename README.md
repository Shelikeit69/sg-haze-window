# sg-haze-window

AI forecast of hourly PM2.5 in Singapore during transboundary haze, to help people pick lower-exposure windows for outdoor activity. Entry to the AI4Climate 2026 Global Youth Climate Solutions Challenge (open track).

**Live demo:** https://shelikeit69.github.io/sg-haze-window/

> Status: work in progress. Sections marked TODO are not yet written. No results are reported until they come out of the code in this repository.

## Problem

TODO

## Users

TODO

## What the AI does

TODO

## Data sources

TODO

## Results

TODO. The model will be compared against a persistence baseline (next hours = current reading). If it does not beat the baseline, this section will say so.

## Limitations and safe use

TODO

## Validation plan

TODO

## Repository layout

```
data/raw/        source data as downloaded, never edited
data/processed/  cleaned, merged tables built by src/
src/             data pipeline, features, model, evaluation
notebooks/       exploration only; nothing reported comes only from a notebook
app/             demo page
docs/            competition submission materials
archive/         superseded versions
```

## License

MIT
