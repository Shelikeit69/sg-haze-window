# Demo video script (target 2:45, limit 3:00)

Screen recording of the live page plus a few slides. About 360 spoken words.

| Time | On screen | Voice-over |
|---|---|---|
| 0:00 | Photo or screen of hazy Singapore skyline (own footage) [TO CONFIRM] | This is Singapore in October 2026. Smoke from fires in Sumatra and Kalimantan has kept the air in NEA's unhealthy range for days at a time. |
| 0:12 | NEA hourly chart for 14 Oct, west region | On the fourteenth, PM2.5 in the west went from 111 at noon to 284 two hours later. If you run or play football outdoors, the question is simple: when should I go? |
| 0:27 | Haze Window page, East selected | Haze Window answers that for each NEA region. It shows the latest reading and the band, and suggests the daytime hour with the lowest forecast in the next 24 hours. |
| 0:45 | Chart: measured line, estimate, shaded error band | The estimate is half the current reading and half the CAMS forecast, rescaled to how far CAMS has been off from NEA readings this season. The shaded band is the typical miss we measured in testing, about 21 micrograms. |
| 1:05 | "How well it worked" table | We picked the method on one period and tested it once on the worst ten days of the season. It missed by 21 on average, against 24 for just repeating the current reading, and got the NEA band right 81 percent of the time. |
| 1:25 | Shadow model toggle switched on | We also trained a machine-learning model on four years of NEA data, weather, NASA fire detections and CAMS. It did not beat repeating the current reading. Singapore had almost no haze from 2023 to 2025, so it has seen one real season. |
| 1:45 | promotion_criteria.md on GitHub | So it runs in shadow mode. It logs a forecast every day and cannot change the advice until it meets criteria we published before any scoring: thirty haze days and a clear win over the simple baseline. |
| 2:05 | Limits section | We also show what we are unsure of. We could not confirm the historical CAMS data was issued in advance, so live results may be worse. Estimates are for regions, not streets. Smoke can arrive within an hour. |
| 2:25 | Validation plan slide | Next, a 90-day pilot with people who exercise outdoors, and a daily log that scores every forecast before the outcome is known. |
| 2:38 | GitHub repo and demo URL | Code, data and every test result are open on GitHub. One place, one problem, and an answer we can check. |
| 2:45 | End | |

Recording notes:
- Record the page while live data is loading, so the status line shows "Live".
- Speak at about 130 words per minute; trim the 2:05 section first if over time.
- Before recording, rerun `src/export_app_data.py` and `src/build_site.py` so the page and this script use the same figures.
