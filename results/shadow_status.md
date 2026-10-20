# Shadow model status (shadow-v1)

Scored at 2026-10-20T00:43:24+00:00 UTC. Criteria: docs/promotion_criteria.md

- Logged predictions with a known outcome: 1100
- Distinct haze days scored (12-24 h): 5 / 30 needed

| Criterion | Met |
|---|---|
| 1. >= 30 haze days | no |
| 2. MAE 37.7 <= 0.9 x persistence 32.2 and < advisor 34.3 | no |
| 3. every region <= 1.1 x persistence (worst 1.45) | no |
| 4. P10-P90 coverage 0.56 in [0.70, 0.90] | no |

**Promote: NO — stays in shadow mode**

## Hour choice (live)

Candidates: 06:00-21:00 in the 24 h after each issue. Saving = mean PM2.5 over the candidates minus PM2.5 at the picked hour (higher is better). Regret = picked minus the lowest candidate (lower is better). Not part of the promotion criteria.

No issue has all candidate hours observed yet.
