# Main Analytical Questions

*Provisional list for Milestone 0. Questions will be revised after Stage 1 (data understanding), once feasibility is confirmed against the real data.*

## Guiding principles

- Each question names the columns involved, a comparison, and a possible conclusion.
- Correlation is not causation. Confounders and limitations are documented for every conclusion.
- Before a question is locked in, check that the data can answer it (for example, how many movies have non-zero budget and revenue).

## Known data caveats that affect many questions

- **`budget` and `revenue`:** `0` usually means missing, not a true zero. Money questions use a smaller sample.
- **`popularity`:** a TMDB score captured when the dataset was scraped, not a lifetime measure. It is skewed and favors recent movies. `vote_count` can serve as an alternative popularity measure.
- **List columns** (`genres`, `production_companies`, `production_countries`, `spoken_languages`, `cast`, `crew`, `keywords`) are many-to-many and need parsing.
- **Outliers** in `runtime` (for example 0 or 900+ minutes) need handling.

---

## 1. Movie economics

| # | Question | Columns | Possible method | Notes / risks |
|---|---|---|---|---|
| E1 | Does a bigger budget guarantee more revenue, or mainly increase the variance of outcomes (more big hits and more big flops)? | `budget`, `revenue` | Correlation, regression, spread by budget bucket | Many zeros; log-transform skewed values |
| E2 | Which genres have the highest median ROI, and which are the riskiest (widest ROI spread)? | `genres`, `budget`, `revenue` | Group by genre, median and IQR | Genre is many-to-many |
| E3 | Has average budget or revenue changed over decades (inflation-adjusted if feasible)? | `release_date`, `budget`, `revenue` | Time series by decade | Inflation data would be external |
| E4 | Do a few production companies account for a large share of total revenue and votes? Do they have higher median ROI, or just higher budgets? | `production_companies`, `revenue`, `budget`, `vote_count` | Concentration (top-N share), ROI comparison | Separates "bigger" from "better" |
| E5 | Are sequels and franchise movies (`belongs_to_collection`) more profitable or higher rated than standalone movies? | `belongs_to_collection`, `revenue`, `vote_average` | Group comparison, hypothesis test | Collection field needs parsing |
| E6 | Do movies from different production countries differ in revenue and rating? | `production_countries`, `revenue`, `vote_average` | Group comparison | Many-to-many; group small countries as "Other" |
| E7 | Does spoken or original language relate to revenue? Do movies with missing language data perform differently? | `original_language`, `spoken_languages`, `revenue` | Group comparison | Use `original_language` as main variable; check whether missing language means low-quality records |

## 2. Audience behaviour

| # | Question | Columns | Possible method | Notes / risks |
|---|---|---|---|---|
| A1 | How does the spread of `vote_average` change as `vote_count` increases? At what vote count does the average stabilize? Is a low-vote rating reliable? | `vote_average`, `vote_count` | Scatter plot, binned variance | Leads to a weighted (Bayesian) rating, also useful for the recommender |
| A2 | Is there a relationship between `runtime` and `popularity` (or `vote_average`)? Linear, or does it peak at a certain length? | `runtime`, `popularity`, `vote_average` | Correlation, binned medians, non-linear fit | Remove runtime outliers first |
| A3 | Do release month and season affect popularity and revenue? | `release_date`, `popularity`, `revenue` | Group by month | Confounded: blockbusters cluster in summer and December |
| A4 | Do movies with a tagline, or a longer overview, have higher popularity? Do missing taglines or overviews signal low-visibility movies? | `tagline`, `overview`, `popularity` | Simple features (`has_tagline`, overview word count), group comparison | Bigger-budget movies may simply have more marketing; NLP is a later step |
| A5 | Do highly rated movies earn more? Is `vote_average` related to `revenue`? | `vote_average`, `revenue` | Correlation, regression | Quality is not the same as commercial success |
| A6 | How are user ratings distributed? Do users tend to rate high (positive skew)? How much do individual rating habits vary? | `ratings.rating`, `userId` | Distributions, per-user mean and variance | Use `ratings_small.csv` first |
| A7 | Do popular movies (high `vote_count`) get rated differently from niche ones? | `vote_count`, `vote_average`, `ratings` | Group comparison | Popularity bias |

## 3. Movie and industry analysis

| # | Question | Columns | Possible method | Notes / risks |
|---|---|---|---|---|
| I1 | How has genre share changed by decade? | `genres`, `release_date` | Share by decade, trend plots | Multi-genre movies counted in each genre |
| I2 | Do certain directors consistently outperform their genre's average rating or ROI? | `crew`, `genres`, `vote_average`, `revenue` | Director vs genre baseline | Need a minimum number of movies per director |
| I3 | Is there a relationship between production company, rating and popularity? | `production_companies`, `vote_average`, `popularity` | Group comparison | Overlaps with E4; may be merged |
| I4 | How have runtime and language mix changed over time? | `runtime`, `original_language`, `release_date` | Trend by decade | Descriptive question |

## 4. Recommendation (must-have)

| # | Question | Data | Possible method | Notes / risks |
|---|---|---|---|---|
| R1 | Can genres, keywords, cast and director alone find movies a person would consider similar? | `genres`, `keywords`, `credits` | TF-IDF, cosine similarity | Content-based baseline |
| R2 | Do users who liked a movie also tend to like its content-based neighbors? | `ratings`, content similarity | Validate recommender against rating history | Uses `links` to join ratings to movies |
| R3 | How much does a user's rating history improve recommendations over content features alone? | `ratings`, content features | Collaborative filtering vs content-based, RMSE, precision@k | Start with `ratings_small.csv` |
| R4 | Does a weighted rating (accounting for `vote_count`) give better "top movies" lists than raw `vote_average`? | `vote_average`, `vote_count` | Bayesian weighted rating | Builds on A1 |

## Stretch

| # | Question | Notes |
|---|---|---|
| S1 | Which features best predict revenue, and how accurate can a simple model be? | Linear regression, Random Forest, gradient boosting; watch for leakage |

---

## Next step: prioritize

The list above is deliberately larger than needed. Pick roughly **8 to 12** questions to commit to:

- 2 to 3 per area
- At least 2 to 3 from Recommendation (a must-have)
- Mark each as **Essential** or **Optional**

| Selected? | Question ID | Priority |
|---|---|---|
| | | |
