# Validation plan (90 days)

## What we want to find out

1. Does the advice hold up on forecasts made in advance? The backtest could not rule out that historical CAMS values had information from after the forecast time. A live log settles this.
2. Do people change when they exercise, and does that lower the PM2.5 they are out in?
3. Does the shadow model get close to its promotion criteria?

## Who takes part

Eight members of the applicant's amateur football team in Singapore, who have agreed to take part. They train outdoors together and need to pick session times. Eight people is a small group: the pilot can show whether the advice is understood and used, not prove a health effect. People with heart or lung conditions are asked to follow NEA's advice and their doctor rather than the tool.

## Setting

Singapore's five NEA regions, starting in the current haze season. The southwest monsoon season usually brings the haze; once the monsoon changes the haze often ends, so the pilot may see few haze days. The plan below allows for that.

## Method

**Weeks 1 to 12, every day: live accuracy log.** `src/shadow.py predict` runs each morning at 05:50 (GitHub Actions) and records, before the outcome is known, three forecasts for every region and the next 24 hours (the advice estimate, repeating the current reading, and the shadow model), plus the hour the page recommends and the hour the shadow model would pick. `src/shadow.py score` compares them with NEA readings once they arrive, including how much cleaner the recommended hour was than the other daytime hours. Days saved before they were complete are downloaded again, so every forecast eventually gets an outcome. Nothing in the log is recomputed later.

**Weeks 1 to 6, while haze lasts: user test.**
- Each participant uses the page before outdoor sessions and records the planned time, the time they actually went, and whether the page changed their plan (a two-question form after each session).
- Exposure is measured with NEA data, not wearable sensors: the 1-hour PM2.5 for their region at the hour they went, compared with the hour they would normally have gone.
- At the end, a short interview: was the advice clear, did the stated error range make sense, what would make them trust it more or less.

**Weeks 7 to 12: review and report.** Write up results, including anything that went badly, and decide whether to continue into the next haze season.

## What counts as success

Decided now, before the pilot starts:

- Live advice estimate has a lower average miss than repeating the current reading, over at least 10 haze days.
- Sessions moved because of the page were, on average, at a lower NEA reading than the participant's usual hour.
- Most participants can correctly say what the error range on the page means.

If there are fewer than 10 haze days in the 90 days, we report the result as inconclusive and keep the daily log running into the next season rather than stretching a small sample.

## Risks

- Too few haze days to judge. Handled by the inconclusive rule above.
- People may take the estimate as exact. The page shows the typical error and tells them to check the live reading; the interview checks whether that worked.
- Data services can change or go down. The page falls back to a saved snapshot and says so.

## Cost

Data and hosting are free (NEA, Open-Meteo, NASA FIRMS, GitHub Pages). The main cost is participants' time: about one minute per session plus one interview.
