# Project statement

**Project:** Haze Window
**Track:** Open track
**Place:** Singapore
**Demo:** https://shelikeit69.github.io/sg-haze-window/
**Code and data:** https://github.com/Shelikeit69/sg-haze-window
**Team:** Zhang Lin Si Cheng (Toni), individual entry

## The problem

Smoke from fires in Sumatra and Kalimantan has pushed Singapore's air into NEA's unhealthy range for days at a time this season. News reports citing NEA put the 24-hour PSI in the central region at 192 on 9 October, the highest this year. In NEA's hourly data, the 1-hour PM2.5 in the west rose from 111 µg/m³ at noon on 14 October to 284 at 14:00. Twenty days between 1 August and 15 October 2026 had a regional daily mean at or above 56 µg/m³, the lower edge of NEA's Elevated band. Between August and mid-November of 2023, 2024 and 2025 there was one such day in total.

People who exercise outdoors have to decide when to go. NEA publishes the current reading and a 24-hour PSI forecast, but neither says which hour later today is likely to be cleaner. Local rain does not settle the question: on the morning of 15 October a heavy thunderstorm passed over Changi, and by 13:00 the 1-hour PM2.5 was still 98 to 152 µg/m³ across the five regions.

## Who it is for

People in Singapore who run, cycle or play sport outdoors, and the people who schedule outdoor sessions for others, such as amateur clubs and coaches. People with heart or lung conditions are told to follow NEA's advice and their doctor; the tool does not replace either.

## What the AI does

The tool answers one question for each NEA region: over the next 24 hours, which daytime hour is likely to have the lowest PM2.5, and roughly how high will it be?

It has two parts.

1. **The advice users see.** The CAMS global air-quality forecast tends to under-read Singapore's haze (in the east, NEA readings this season have been 1.26 times the CAMS value at the median). The tool rescales CAMS against NEA readings from the current season, then estimates each coming hour as half the current NEA reading and half the rescaled forecast. The suggested hour is the daytime hour with the lowest forecast.
2. **A machine-learning model in shadow mode.** A gradient-boosting model trained on NEA readings, weather, NASA satellite fire detections and CAMS (August to November 2023 to 2025, plus August to October 2026) makes a 1 to 24 hour forecast with a P10 to P90 range every day. In testing it did not beat simply repeating the current reading, so it does not affect the advice. Its forecasts are logged and scored against later NEA readings, and it is switched on only if it meets criteria we published before scoring began.

## Where AI fits

Choosing the hour needs a forecast of how smoke will move over the next day, and that depends on fires and winds hundreds of kilometres away. Local readings alone cannot see that coming, which is why our model trained on Singapore data failed. CAMS, a numerical forecast run by the European Centre for Medium-Range Weather Forecasts, models the transport but under-reads Singapore's haze. The advice users see today is a corrected CAMS forecast checked against held-out data, which is a statistical method rather than machine learning.

The machine-learning model is the part that should improve with time. It learns how satellite fire detections, winds and CAMS relate to what NEA later measures, and every new haze season adds training examples. Until it proves itself on predictions made in advance, it stays in shadow mode. We would rather ship a simpler method that tested well than a model that did not.

## What testing showed

The method was tuned on 26 September to 5 October 2026 and tested once on 6 to 15 October, the worst haze stretch of the year.

- PM2.5 level estimate: average miss of 21.1 µg/m³, against 24.4 for repeating the current reading. NEA band correct 81 % of the time, against 73 %.
- Suggested hour: on average 12.1 µg/m³ lower than a random daytime hour.
- A fixed morning hour each day did slightly better on the test days (13.1) but worse in validation.
- The machine-learning model missed by 36.4 µg/m³ at 13 to 24 hours ahead, against 31.9 for repeating the reading.

The test covers ten days, and the five regions move together, so these are rough figures. We could not confirm that historical CAMS values were issued before the hours they forecast, so results that use CAMS may be better than live use will be.

## Who benefits and what it costs

The people who benefit are those who exercise outdoors, and the coaches and amateur clubs who set session times for others. The first users are the eight members of an amateur football team in the pilot.

Running it today costs nothing. The page is hosted on GitHub Pages, and the twice-daily run uses GitHub Actions, which is free for public repositories. NEA data is used under the Singapore Open Data Licence, which allows commercial use with attribution. NASA FIRMS fire data needs only a free key. CAMS forecasts and weather come from Open-Meteo, which is free for non-commercial use up to 10,000 calls a day, with attribution under CC BY 4.0.

That last point limits how the tool can grow. Commercial use would need a paid Open-Meteo subscription or another source of CAMS data. The realistic path for now is a free public tool that costs almost nothing to keep running. Who might pay later is an open question: venues and organisers that schedule outdoor sessions, or employers with outdoor workers, are possible candidates, but we have not approached any of them. The pilot interviews ask the coach and players whether they would keep using the tool, which is the first test of whether anyone values it.

## Where else it works

The method needs two inputs: hourly PM2.5 from local monitors and the CAMS forecast, which covers the whole world. Any place with both can run the same estimate, with its own correction ratio worked out from local readings. Johor and other parts of Malaysia that receive the same smoke are the obvious next step. Malaysia publishes its own air pollutant index, which is calculated differently from Singapore's PSI, so the method would use raw PM2.5 concentrations only. Each new place needs its own backtest before anyone relies on it: the Singapore test results do not carry over.

## What we learned

In 2023 to 2025 the cleanest daytime hour in the east fell between 12:00 and 15:00, but the spread across the day was only 3 to 8 µg/m³. In 2026 the east was lowest in the morning (07:00 on non-haze days, 09:00 on haze days), with a 24 µg/m³ spread on haze days. Because the earlier years supply most of the data, a fixed-hour rule built from all four years pointed people to the afternoon and did worse on the test days. Daily patterns from clean years do not carry over to a haze season.
