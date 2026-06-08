# UberEats Promo Analysis

End-to-end data pipeline analysing promotional strategies across 367 Sydney restaurants on UberEats.

## Key Finding
Promotions are a signal of struggle, not success. Restaurants running promos have systematically lower ratings (4.03 vs 4.46, p<0.0001) suggesting discounts compensate for poor reputation rather than build it.

## Tech Stack
| Layer | Tool |
|-------|------|
| Scraping | Python + Playwright |
| Pipeline | dbt + DuckDB Bronze to Silver to Gold |
| Statistical Analysis | Python scipy statsmodels |
| Visualisation | Power BI |

## Statistical Results
| Hypothesis | Result | Finding |
|---|---|---|
| H1: Promo restaurants have lower ratings | Significant p<0.0001 | 4.03 vs 4.46 gap |
| H2: Promo restaurants have more reviews | Not significant p=0.224 | No evidence promos drive volume |
| H3: Low-rated restaurants run more promos | Supported | Promos compensate for poor reputation |
| Regression net effect | Not significant p=0.617 | Rating gap is selection not causation |

## Business Insight
After controlling for suburb and delivery fee, promotions have no significant net effect on ratings. The restaurants most likely to run promotions are already underperforming. Discounts are a symptom of a quality problem, not a solution to it.

## Data
367 restaurants across 5 Sydney suburbs CBD, Parramatta, Surry Hills, Chatswood, Newtown scraped June 2026.

## Limitations
- Observational data, no causal identification
- Single time-point snapshot June 2026
- 5 suburbs only
- Small sample sizes for some promo types
