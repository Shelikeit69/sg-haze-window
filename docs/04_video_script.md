# Demo video script (Chinese voice-over, English subtitles, limit 3:00)

Record one clip per segment and name the files 01 to 12 (for example 01.m4a). Read the Chinese text as written so the subtitles match. Leave about half a second of silence at the start and end of each clip. Each picture stays on screen exactly as long as its clip.

| # | Picture | 中文配音 | English subtitle |
|---|---|---|---|
| 01 | Slide 1, cover | 大家好，我是张林思成。Haze Window 帮新加坡人在烟霾季节，挑一个空气相对干净的时段出门运动。 | Hi, I'm Zhang Lin Si Cheng. Haze Window helps people in Singapore pick a cleaner hour to exercise outdoors during the haze season. |
| 02 | Slide 2, 14 Oct chart | 今年十月，印尼的火灾烟霾一次次飘到新加坡。十月十四号中午，西部的 PM2.5 是 111，两小时后升到 284。今年已经有 20 天达到 NEA 的 Elevated 等级以上，前三年同期加起来只有 1 天。 | This October, smoke from fires in Indonesia kept drifting into Singapore. At noon on 14 October, PM2.5 in the west was 111. Two hours later it was 284. This year 20 days have reached NEA's Elevated band or worse; the same months of the previous three years had one. |
| 03 | Slide 3, the decision | 在户外踢球、跑步的人，每天都要决定几点出门。NEA 公布当前读数，但不会告诉你今天哪个小时更干净。下雨也不一定管用。 | People who play football or run outdoors have to decide when to go. NEA publishes the current reading, but not which hour later today will be cleaner. Rain does not always help. |
| 04 | Website recording | 这是我们的网站。选一个区，能看到当前读数和 NEA 等级、过去 12 小时的实测和未来 24 小时的估计。圆圈是推荐时段，阴影是测试中的平均误差，大约正负 21。出门前，页面会提醒你再看一次实时读数。 | This is the website. Pick a region to see the current reading and NEA band, the last 12 hours measured and the next 24 hours estimated. The circle marks the suggested hour; the shading is the average miss in testing, about plus or minus 21. The page reminds you to check the live reading before you go. |
| 05 | Slide 4, method | 方法很简单。欧洲的 CAMS 预报对新加坡烟霾普遍估低，我们用本季实测校正它，再和当前读数各取一半，作为每个小时的估计。 | The method is simple. Europe's CAMS forecast tends to under-read Singapore's haze, so we rescale it with this season's readings and average it half and half with the current reading. |
| 06 | Slide 5, results | 我们拿今年烟霾最重的十天只测一次。平均误差 21.1，比直接沿用当前读数的 24.4 小，NEA 等级判断对了 81%。推荐时段比随便挑一个白天时段平均低 12.1。测试只有十天，数字只能参考。 | We tested once on the ten worst haze days of the year. The average miss was 21.1, against 24.4 for repeating the current reading, and the NEA band was right 81% of the time. The suggested hour was 12.1 lower than a random daytime hour. Ten days is a small test, so treat these as rough figures. |
| 07 | Slide 6, ML model | 我们也训练了机器学习模型，用了四年数据和卫星火点，但它没有赢过直接沿用当前读数。前三年新加坡几乎没有烟霾，模型只见过今年这一次。 | We also trained a machine-learning model on four years of data and satellite fire detections. It did not beat repeating the current reading. Singapore had almost no haze in the previous three years, so the model has seen only this one. |
| 08 | Slide 7, shadow mode | 所以它现在是影子模式：每天早晚自动记录预测，但不影响给用户的建议。至少 30 个烟霾日里明显赢过基准，才会启用。这些标准在评分前就已公开。 | So it runs in shadow mode. Every morning and evening it logs a forecast, but it does not change the advice. It is switched on only after it clearly beats the baseline over at least 30 haze days. We published these rules before any scoring. |
| 09 | Slide 8, limits | 不确定的地方我们也写清楚了：历史预报的发布时间无法确认，实时效果可能更差；估计只到分区；烟霾可能一小时内就到。 | We also state what we are unsure of. We could not confirm when past forecasts were issued, so live results may be worse. Estimates cover regions, not streets. Smoke can arrive within an hour. |
| 10 | Slide 9, pilot | 接下来 90 天，请足球队 8 位队友试用，看他们是否因此改了出门时间。8 个人很少，只能检验建议有没有被看懂、被使用。 | Over the next 90 days, eight of my football teammates will try it, and we will see whether it changes when they go out. Eight people is few: this tests whether the advice is understood and used. |
| 11 | Slide 10, cost and reach | 目前运行成本为零，但 CAMS 的免费版只限非商业用途，谁愿意付费还没有验证。同样的方法可以用到柔佛等地，但每个地方都要先单独回测。 | It costs nothing to run today, but the free CAMS feed is for non-commercial use only, and we have not tested who would pay. The method could work in Johor and elsewhere, but each place needs its own backtest first. |
| 12 | Slide 11, links | 代码、数据和每一次测试结果都公开在 GitHub。一个地方，一个气候问题，一个可以检验的答案。谢谢。 | The code, the data and every test result are open on GitHub. One place, one climate problem, and an answer you can check. Thank you. |

## Recording tips
- Use the phone's voice memo app in a quiet room, phone about 20 cm from your mouth.
- If a clip goes wrong, re-record only that clip.
- Numbers to read as written: 111, 284, 20, 1, 21.1, 24.4, 81%, 12.1, 30, 90, 8.

## Submitted version
The submitted video has no voice-over. It shows the Chinese text above as burned-in subtitles. Each segment runs for its Chinese character count / 4.5 s, plus padding (167.7 s in total):

    python src/video/assemble.py --work DIR --pdf slides.pdf --preview --subs zh --name haze_window_demo_zh.mp4

## Assembly (done in code)
- Slide pictures come from the exported 11-page PDF, so fonts and layout match the deck.
- Segment 04 is a recording of the live website, made with a headless browser.
- Subtitles are burned in at the bottom; output MP4, 1920 x 1080.
