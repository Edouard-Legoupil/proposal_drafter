# Proposal Drafter Metrics API Reference

This document details the API contract for dashboard metrics, analytical depth for each endpoint, and advanced brainstorming of valuable analytics for ongoing platform growth. 

Each endpoint **must return the listed structure**; use valid empty arrays or zeroes when no data, never null/undefined.

- Endpoints must support rich filtering (time, status, type, author, team, donor, donor group).
- Aggregate and granular payloads should be easy to consume for graphing/reporting.
- Enable drilldown and comparative APIs (top N, quartile, anomaly-find).
- All endpoints return valid shape/payload even if no data.

---
---
## Pipeline Management (Consolidated)

### /api/metrics/pipeline-kpis
**Description:** Consolidated KPIs for the pipeline overview. Support rich filtering. Excludes deleted proposals by default unless explicitly filtered.
**SQL Query:**
```sql
WITH filtered_proposals AS (
    SELECT p.*, 
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
            ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
        END as budget_value
    FROM proposals p
    {WHERE_CLAUSE}
),
cycle_times AS (
    SELECT 
        p.id,
        EXTRACT(EPOCH FROM (
            SELECT MIN(created_at) FROM proposal_status_history WHERE proposal_id = p.id AND status = 'submitted'
        ) - p.created_at) as seconds_to_submit
    FROM filtered_proposals p
),
counts AS (
    SELECT 
        COALESCE(SUM(budget_value), 0) as total_funding,
        COUNT(*) as total_proposals,
        COUNT(DISTINCT (SELECT donor_id FROM proposal_donors WHERE proposal_id = p.id LIMIT 1)) as total_donors,
        COUNT(DISTINCT p.user_id) as total_users,
        COUNT(*) FILTER (WHERE status = 'in_review') as count_under_review,
        COUNT(*) FILTER (WHERE status = 'submitted') as count_submitted,
        COUNT(*) FILTER (WHERE status = 'deleted') as count_deleted
    FROM filtered_proposals p
)
SELECT 
    total_funding,
    total_proposals,
    CASE WHEN total_proposals > 0 THEN total_funding / total_proposals ELSE 0 END as avg_value,
    total_donors,
    (SELECT COUNT(*) FROM teams) as total_teams,
    total_users,
    CASE WHEN total_proposals > 0 THEN (count_under_review::float / total_proposals) * 100 ELSE 0 END as pct_under_review,
    CASE WHEN total_proposals > 0 THEN (count_submitted::float / total_proposals) * 100 ELSE 0 END as pct_submitted,
    CASE WHEN total_proposals > 0 THEN (count_deleted::float / total_proposals) * 100 ELSE 0 END as pct_deleted,
    COALESCE((SELECT AVG(seconds_to_submit) FROM cycle_times WHERE seconds_to_submit IS NOT NULL), 0) as avg_cycle_time
FROM counts;
```
**Payload:**
```json
{
  "total_funding": 1250000.0,
  "total_proposals": 45,
  "avg_value": 27777.77,
  "total_donors": 12,
  "total_teams": 5,
  "total_users": 28,
  "pct_under_review": 15.5,
  "pct_submitted": 45.0,
  "pct_deleted": 5.0,
  "avg_cycle_time": 1080000
}
```

### /api/metrics/proposals-by-donor
**Description:** Total value and counts per donor. Excludes deleted proposals by default.
**SQL Query:**
```sql
SELECT 
    d.name as donor,
    SUM(CASE 
        WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
        WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
        ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
    END) as total_value,
    COUNT(p.id) as proposal_count,
    COUNT(p.id) FILTER (WHERE p.status = 'submitted') as submitted_count
FROM proposals p
JOIN proposal_donors pd ON p.id = pd.proposal_id
JOIN donors d ON pd.donor_id = d.id
{WHERE_CLAUSE}
GROUP BY d.name
ORDER BY total_value DESC;
```
**Payload:**
```json
[
  { "donor": "ECHO", "total_value": 500000, "proposal_count": 10, "submitted_count": 8 },
  ...
]
```

### /api/metrics/proposals-by-outcome
**Description:** Heatmap data showing outcome references per donor. Excludes deleted proposals by default.
**SQL Query:**
```sql
SELECT 
    d.name as donor,
    o.name as outcome,
    COUNT(p.id) as count
FROM proposals p
JOIN proposal_donors pd ON p.id = pd.proposal_id
JOIN donors d ON pd.donor_id = d.id
JOIN proposal_outcomes po ON p.id = po.proposal_id
JOIN outcomes o ON po.outcome_id = o.id
{WHERE_CLAUSE}
GROUP BY d.name, o.name
ORDER BY count DESC;
```
**Payload:**
```json
[
  { "donor": "ECHO", "outcome": "Protection", "count": 15 },
  ...
]
```

### /api/metrics/proposals-by-context
**Description:** Treemap data for field context, aggregated by region.
**SQL Query:**
```sql
SELECT 
    fc.unhcr_region as region,
    fc.name as context,
    SUM(CASE 
        WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
        WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
        ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
    END) as total_value,
    COUNT(p.id) as proposal_count,
    COUNT(p.id) FILTER (WHERE p.status = 'submitted') as submitted_count
FROM proposals p
JOIN proposal_field_contexts pfc ON p.id = pfc.proposal_id
JOIN field_contexts fc ON pfc.field_context_id = fc.id
{WHERE_CLAUSE}
GROUP BY fc.unhcr_region, fc.name
ORDER BY total_value DESC;
```
**Payload:**
```json
[
  { "region": "Middle East", "context": "Jordan", "total_value": 200000, "proposal_count": 5, "submitted_count": 4 },
  ...
]
```

### /api/metrics/proposals-by-team
**Description:** Stacked bar data showing proposal value per team by status.
**SQL Query:**
```sql
WITH base_data AS (
    SELECT 
        tm.name as team_name,
        p.status,
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
            ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
        END as budget_value,
        p.id as proposal_id
    FROM proposals p
    JOIN users u ON p.user_id = u.id
    JOIN teams tm ON u.team_id = tm.id
    {WHERE_CLAUSE}
),
team_totals AS (
    SELECT 
        team_name,
        COUNT(proposal_id) as total_proposals
    FROM base_data
    GROUP BY team_name
)
SELECT 
    bd.team_name || ' (' || tt.total_proposals || ')' as team,
    bd.status,
    SUM(bd.budget_value) as value,
    COUNT(bd.proposal_id) as count,
    COUNT(bd.proposal_id) FILTER (WHERE bd.status = 'submitted') as submitted_count
FROM base_data bd
JOIN team_totals tt ON bd.team_name = tt.team_name
GROUP BY bd.team_name, tt.total_proposals, bd.status
ORDER BY SUM(bd.budget_value) OVER (PARTITION BY bd.team_name) DESC, bd.team_name, value DESC;
```
**Payload:**
```json
[
  { "team": "Team A", "status": "draft", "value": 50000, "count": 2, "submitted_count": 0 },
  ...
]
```

### /api/metrics/proposals-by-time
**Description:** Stacked area data showing total value per status over time.
**SQL Query:**
```sql
SELECT 
    TO_CHAR(p.created_at, 'YYYY-MM') as period,
    p.status,
    SUM(CASE 
        WHEN p.form_data->>'Budget Range' ~* 'k' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000)
        WHEN p.form_data->>'Budget Range' ~* 'M' THEN (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric * 1000000)
        ELSE NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]', '', 'g'), '')::numeric
    END) as value
FROM proposals p
{WHERE_CLAUSE}
GROUP BY period, p.status
ORDER BY period ASC;
```
**Payload:**
```json
[
  { "period": "2024-01", "status": "draft", "value": 100000 },
  ...
]
```

## Collaboration

#### /api/metrics/edit-activity
*Distribution of proposals by number of recorded edits (using proposal_status_history entries).*
**SQL Query:**
```sql
SELECT edit_count, COUNT(proposal_id) as proposal_count
FROM (
    SELECT proposal_id, COUNT(psh.id) as edit_count
    FROM proposal_status_history psh
    JOIN proposals p ON psh.proposal_id = p.id
    {WHERE_CLAUSE}
    GROUP BY proposal_id
) t
GROUP BY edit_count
ORDER BY edit_count;
```
**Payload:**
```json
{
  "labels": ["1 edit", "2 edits", "5 edits"],
  "data": [10, 25, 5]
}
```

#### /api/metrics/reviewer-activity
*Distribution of proposals by number of review cycles (using 'in_review' status history entries).*
**SQL Query:**
```sql
SELECT review_count, COUNT(proposal_id) as proposal_count
FROM (
    SELECT proposal_id, COUNT(psh.id) as review_count
    FROM proposal_status_history psh
    JOIN proposals p ON psh.proposal_id = p.id
    WHERE psh.status = 'in_review'
    {AND_WHERE_CLAUSE}
    GROUP BY proposal_id
) t
GROUP BY review_count
ORDER BY review_count;
```
**Payload:**
```json
{
  "labels": ["0 reviews", "1 review", "2 reviews"],
  "data": [15, 30, 8]
}
```

---
### Edge Contract Cases
- **Numbers always returned:** Use 0 for numeric results if empty, never null.
- **Arrays always returned:** Use empty arrays, never null or undefined.
- **Top-level keys always present:** Never omit the documented keys from the payload.

---
## Knowledge Metrics

### /api/metrics/knowledge-cards
**Description:** Number of knowledge cards by type/time/team/author.
**Questions Answered:** Who/what drives content? Where are the gaps?
**SQL Query:**
```sql
SELECT kc.type, COUNT(kc.id) as count 
FROM knowledge_cards kc 
GROUP BY kc.type;
```
```json
{
  "types": ["Policy", "Research"],
  "counts": [5, 12]
}
```


### /api/metrics/knowledge-cards-history
**Description:** Revision frequency and total revisions per card/type.
**Questions Answered:** Which cards are most curated? Any maintenance patterns?
**SQL Query:**
```sql
SELECT kc.id as card_id, COUNT(kr.id) as revisions 
FROM knowledge_card_history kr 
JOIN knowledge_cards kc ON kr.knowledge_card_id = kc.id 
GROUP BY kc.id;
```
```json
{
  "card_ids": ["kc-1", "kc-2"],
  "revisions": [7, 23]
}
```

### /api/metrics/reference
**Description:** Number of external URLs referenced per card/type.
**Questions Answered:** Who cites most? Which types rely on outside info?
**SQL Query:**
```sql
SELECT kc.type, COUNT(kcr.id) as references 
FROM knowledge_card_references kcr 
JOIN knowledge_card_to_references kctr ON kcr.id = kctr.reference_id 
JOIN knowledge_cards kc ON kctr.knowledge_card_id = kc.id 
GROUP BY kc.type;
```
```json
{
  "types": ["Policy", "Research"],
  "references": [8, 14]
}
```

### /api/metrics/reference-usage
**Description:** URLs reused across multiple cards, highlighting foundational resources.
**Questions Answered:** Which references are most central? Any silos or overlap?
**SQL Query:**
```sql
SELECT kcr.url, COUNT(DISTINCT kctr.knowledge_card_id) as usage_count 
FROM knowledge_card_references kcr 
JOIN knowledge_card_to_references kctr ON kcr.id = kctr.reference_id 
GROUP BY kcr.url 
HAVING COUNT(DISTINCT kctr.knowledge_card_id) > 1;
```
```json
{
  "urls": ["http://example.org/a", "http://abc.com/b"],
  "usage_counts": [4, 2]
}
```

### /api/metrics/reference-issue
**Description:** Bad/missing references (un-ingested, errors) by type/team.
**Questions Answered:** Where does reference integrity break down?
```json
{
  "error_types": ["NotIngested", "Error"],
  "counts": [3, 1]
}
```

### /api/metrics/card-edit-frequency
*Edit cadence per card/team (average edits/month).*
**SQL Query:**
```sql
SELECT kc.id as card_id, 
       COUNT(kr.id)/GREATEST(1, EXTRACT(MONTH FROM AGE(NOW(), kc.created_at))) as edit_frequency 
FROM knowledge_card_history kr 
JOIN knowledge_cards kc ON kr.knowledge_card_id = kc.id 
GROUP BY kc.id, kc.created_at;
```
```json
{
  "card_ids": ["kc-1", "kc-2"],
  "edit_frequency": [3.1, 0.8]
}
```

### /api/metrics/card-impact-score
*Aggregate views or usages for each card.*
```json
{
  "card_ids": ["kc-1", "kc-2"],
  "impact_scores": [36, 7]
}
```

### /api/metrics/knowledge-silos
*Cards/references only used by one team/cluster*.
**SQL Query:**
```sql
SELECT kc.id as isolated_card_id, t.name as silo_team 
FROM knowledge_cards kc 
JOIN users u ON kc.created_by = u.id 
JOIN teams t ON u.team_id = t.id 
WHERE kc.id IN (
    SELECT kctr.knowledge_card_id 
    FROM knowledge_card_to_references kctr 
    GROUP BY kctr.knowledge_card_id 
    HAVING COUNT(DISTINCT kctr.reference_id) = 1
);
```
```json
{
  "isolated_card_ids": ["kc-3"],
  "silo_teams": ["TeamZ"]
}
```

