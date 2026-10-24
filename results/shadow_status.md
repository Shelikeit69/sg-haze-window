# Shadow model status (shadow-v1)

Scored at 2026-10-24T23:46:40+00:00 UTC. Criteria: docs/promotion_criteria.md

- Logged predictions with a known outcome: 2305
- Distinct haze days scored (12-24 h): 9 / 30 needed

| Criterion | Met |
|---|---|
| 1. >= 30 haze days | no |
| 2. MAE 30.3 <= 0.9 x persistence 27.5 and < advisor 25.6 | no |
| 3. every region <= 1.1 x persistence (worst 1.29) | no |
| 4. P10-P90 coverage 0.63 in [0.70, 0.90] | no |

**Promote: NO — stays in shadow mode**

## Hour choice (live)

Candidates: 06:00-21:00 in the 24 h after each issue. Saving = mean PM2.5 over the candidates minus PM2.5 at the picked hour (higher is better). Regret = picked minus the lowest candidate (lower is better). Not part of the promotion criteria.

No issue has all candidate hours observed yet.
