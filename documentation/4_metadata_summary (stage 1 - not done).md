# Movie Dataset Data Quality Report

## credits.csv

**Row count:** 45476
**Column count:** 3

| Column | Pandas dtype | Dtype Should be | Missing | Unique | Min |    Max | Duplicates |
| ------ | ------------ | --------------- | ------: | -----: | --: | -----: | ---------: |
| cast   | str          | list[dict]      |       0 |  43019 |   - |      - |       2457 |
| crew   | str          | list[dict]      |       0 |  44669 |   - |      - |        807 |
| id     | int64        | -               |       0 |  45432 |   2 | 469172 |         44 |

---

## keywords.csv

**Row count:** 46419
**Column count:** 2

| Column   | Pandas dtype | Dtype Should be | Missing | Unique | Min |    Max | Duplicates |
| -------- | ------------ | --------------- | ------: | -----: | --: | -----: | ---------: |
| id       | int64        | -               |       0 |  45432 |   2 | 469172 |        987 |
| keywords | str          | list[dict]      |       0 |  25989 |   - |      - |      20430 |

---

## links_small.csv

**Row count:** 9125
**Column count:** 3

| Column  | Pandas dtype | Dtype Should be | Missing | Unique | Min |      Max | Duplicates |
| ------- | ------------ | --------------- | ------: | -----: | --: | -------: | ---------: |
| movieId | int64        | -               |       0 |   9125 |   1 |   164979 |          0 |
| imdbId  | int64        | -               |       0 |   9125 | 417 |  5794766 |          0 |
| tmdbId  | float64      | Int64           |      13 |   9112 | 2.0 | 416437.0 |         12 |

---

## links.csv

**Row count:** 45843
**Column count:** 3

| Column  | Pandas dtype | Dtype Should be | Missing | Unique | Min |      Max | Duplicates |
| ------- | ------------ | --------------- | ------: | -----: | --: | -------: | ---------: |
| movieId | int64        | -               |       0 |  45843 |   1 |   176279 |          0 |
| imdbId  | int64        | -               |       0 |  45843 |   1 |  7158814 |          0 |
| tmdbId  | float64      | Int64           |     219 |  45594 | 2.0 | 469172.0 |        248 |

---

## movies_metadata.csv

**Row count:** 45466
**Column count:** 24

| Column                | Pandas dtype | Dtype Should be      | Missing | Unique | Min |          Max | Duplicates |
| --------------------- | ------------ | -------------------- | ------: | -----: | --: | -----------: | ---------: |
| adult                 | str          | bool                 |       0 |      5 |   - |            - |      45461 |
| belongs_to_collection | str          | dict                 |   40972 |   1698 |   - |            - |      43767 |
| budget                | str          | float                |       0 |   1226 |   - |            - |      44240 |
| genres                | str          | list[dict]           |       0 |   4069 |   - |            - |      41397 |
| homepage              | str          | -                    |   37684 |   7673 |   - |            - |      37792 |
| id                    | str          | int64                |       0 |  45436 |   - |            - |         30 |
| imdb_id               | str          | -                    |      17 |  45417 |   - |            - |         48 |
| original_language     | str          | Enum (with all lang) |      11 |     92 |   - |            - |      45373 |
| original_title        | str          | -                    |       0 |  43373 |   - |            - |       2093 |
| overview              | str          | -                    |     954 |  44307 |   - |            - |       1158 |
| popularity            | object       | float64              |       5 |  44176 |   - |            - |       1289 |
| poster_path           | str          | -                    |     386 |  45024 |   - |            - |        441 |
| production_companies  | str          | list[dict]           |       3 |  22708 |   - |            - |      22757 |
| production_countries  | str          | list[dict]           |       3 |   2393 |   - |            - |      43072 |
| release_date          | str          | datetime             |      87 |  17336 |   - |            - |      28129 |
| revenue               | float64      | -                    |       6 |   6863 | 0.0 | 2787965087.0 |      38602 |
| runtime               | float64      | -                    |     263 |    353 | 0.0 |       1256.0 |      45112 |
| spoken_languages      | str          | list[dict]           |       6 |   1931 |   - |            - |      43534 |
| status                | str          | Bool/ enum           |      87 |      6 |   - |            - |      45459 |
| tagline               | str          | -                    |   25054 |  20283 |   - |            - |      25182 |
| title                 | str          | -                    |       6 |  42277 |   - |            - |       3188 |
| video                 | object       | bool                 |       6 |      2 |   - |            - |      45463 |
| vote_average          | float64      | -                    |       6 |     92 | 0.0 |         10.0 |      45373 |
| vote_count            | float64      | -                    |       6 |   1820 | 0.0 |      14075.0 |      43645 |

---

## ratings_small.csv

**Row count:** 100004
**Column count:** 4

| Column    | Pandas dtype | Dtype Should be | Missing | Unique |       Min |        Max | Duplicates |
| --------- | ------------ | --------------- | ------: | -----: | --------: | ---------: | ---------: |
| userId    | int64        | -               |       0 |    671 |         1 |        671 |      99333 |
| movieId   | int64        | -               |       0 |   9066 |         1 |     163949 |      90938 |
| rating    | float64      | -               |       0 |     10 |       0.5 |        5.0 |      99994 |
| timestamp | int64        | datetime        |       0 |  78141 | 789652009 | 1476640644 |      21863 |

---

## ratings.csv

**Row count:** 26024289
**Column count:** 4

| Column    | Pandas dtype | Dtype Should be | Missing |   Unique |       Min |        Max | Duplicates |
| --------- | ------------ | --------------- | ------: | -------: | --------: | ---------: | ---------: |
| userId    | int64        | -               |       0 |   270896 |         1 |     270896 |   25753393 |
| movieId   | int64        | -               |       0 |    45115 |         1 |     176275 |   25979174 |
| rating    | float64      | -               |       0 |       10 |       0.5 |        5.0 |   26024279 |
| timestamp | int64        | datetime        |       0 | 20549435 | 789652004 | 1501829870 |    5474854 |
