# Proposal Drafter Metrics API Reference

This document details the API contract for dashboard metrics, analytical depth for each endpoint, and advanced brainstorming of valuable analytics for ongoing platform growth. 

## 🎯 Metrics Endpoint Contract
Each endpoint **must return the listed structure**; use valid empty arrays or zeroes when no data, never null/undefined.


- Endpoints must support rich filtering (time, status, type, author, donor, category).
- Aggregate and granular payloads should be easy to consume for graphing/reporting.
- Enable drilldown and comparative APIs (top N, quartile, anomaly-find).
- All endpoints return valid shape/payload even if no data.



---
## 🔍 Proposal Pipeline Metrics

### 1. /api/metrics/average-funding-amount
**Description:** Average proposal count and funding value. Supports filtering by status, time, type, author (team/individual).
**Questions Answered:** What is the mean funding requested/awarded? Who has highest/lowest averages? How do averages trend by status/type?
**SQL Query:**
```sql
SELECT 
    AVG(
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN 
                (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]+', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN 
                (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]+', '', 'g'), '')::numeric * 1000000)
            ELSE 
                NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]+', '', 'g'), '')::numeric
        END
    ) as avg_funding 
FROM proposals p
WHERE p.form_data->>'Budget Range' IS NOT NULL 
AND p.form_data->>'Budget Range' != '';
```
**Sample Output:**
```json
{ "amount": 59124 }  // or { "amount": 0 }
```

---
### 2. /api/metrics/proposal-volume
**Description:** Total proposals and funding by category. Slice by status, time, type, author.
**Questions Answered:** Are proposal submissions rising/falling? Which categories/groups are most active?
**SQL Query:**
```sql
SELECT COALESCE(p.form_data->>'Category', p.template_name) as category, 
       COUNT(p.id) as proposal_count 
FROM proposals p 
GROUP BY category 
ORDER BY proposal_count DESC;
```
**Sample Output:**
```json
{
  "categories": ["proposal_template_unhcr.json", "proposal_template_echo.json", "proposal_template_japan.json"],
  "counts": [7, 9, 3]
}

---
### 3. /api/metrics/funding-by-category

**Description:** Aggregate funding per proposal category. Slice by status, time, type, author.
**Questions Answered:** Which project types attract most/least funding? Any trends by team/status over time?
**SQL Query:**
```sql
SELECT 
    COALESCE(p.form_data->>'Category', p.template_name) as category,
    SUM(
        CASE 
            WHEN p.form_data->>'Budget Range' ~* 'k' THEN 
                (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]+', '', 'g'), '')::numeric * 1000)
            WHEN p.form_data->>'Budget Range' ~* 'M' THEN 
                (NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]+', '', 'g'), '')::numeric * 1000000)
            ELSE 
                NULLIF(regexp_replace(p.form_data->>'Budget Range', '[^0-9.]+', '', 'g'), '')::numeric
        END
    ) as total_amount 
FROM proposals p 
WHERE p.form_data->>'Budget Range' IS NOT NULL 
  AND p.form_data->>'Budget Range' != ''
GROUP BY COALESCE(p.form_data->>'Category', p.template_name)
ORDER BY total_amount DESC;
```
**Sample Output:**
```json
{
  "categories": ["proposal_template_unhcr.json", "proposal_template_echo.json", "proposal_template_japan.json"],
  "amounts": [30000, 24000, 5124]
}
```

---
### 4. /api/metrics/donor-interest
**Description:** Donor interaction—number/value of proposals per donor. Slice by status, time, type, author.
**Questions Answered:** Which donors are most engaged? Are interests shifting over time?
**SQL Query:**
```sql
SELECT d.name as donor, COUNT(p.id) as interest 
FROM proposals p 
JOIN proposal_donors pd ON p.id = pd.proposal_id 
JOIN donors d ON pd.donor_id = d.id 
GROUP BY d.name 
ORDER BY interest DESC;
```
**Sample Output:**
```json
{
  "donors": ["Alice Fund", "Bob Foundation"],
  "interest": [5, 12]
}
```

---
### 5. /api/metrics/development-time
**Description:** Average duration proposals spend in each status (draft, submitted, funded, etc.) by team/type/author.
**Questions Answered:** Where do proposals bottleneck? How efficient are teams/types?
**SQL Query:**
```sql
WITH status_durations AS (
    SELECT psh.proposal_id, 
           psh.status, 
           LEAD(psh.created_at, 1, CURRENT_TIMESTAMP) OVER (PARTITION BY psh.proposal_id ORDER BY psh.created_at) - psh.created_at AS duration 
    FROM proposal_status_history psh 
    JOIN proposals p ON psh.proposal_id = p.id
) 
SELECT status, EXTRACT(EPOCH FROM AVG(duration)) as average_duration_seconds 
FROM status_durations 
GROUP BY status;
```
**Sample Output:**
```json
[
  { "status": "Draft", "average_duration_seconds": 259200 },
  { "status": "Submitted", "average_duration_seconds": 86400 }
]
```

---
### 6. /api/metrics/proposal-trends
**Description:** Time-based trends—volume/status of proposals by donor, type, author/team.
**Questions Answered:** When do volumes peak? What trends appear by team or donor over time?
**SQL Query:**
```sql
SELECT TO_CHAR(p.created_at, 'YYYY-MM') as period, 
       p.status, 
       COUNT(p.id) as proposal_count 
FROM proposals p 
GROUP BY period, p.status 
ORDER BY period DESC;
```
**Sample Output:**
```json
{
  "timeline": ["2024-01", "2024-02", "2024-03"],
  "statuses": ["Submitted", "Funded", "Rejected"],
  "counts": [14, 7, 3]
}
```

---
### Additional Advanced Pipeline Metrics

#### /api/metrics/conversion-rate
*Success ratio (submitted vs approved/funded) by filter.*
**SQL Queries:**
```sql
-- Total
SELECT COUNT(id) FROM proposals;
-- Approved
SELECT COUNT(id) FROM proposals WHERE status = 'approved';
```
```json
{ "rate": 0.41 }
```

#### /api/metrics/abandonment-rate
*Proposals started but not submitted/funded.*
**SQL Queries:**
```sql
-- Total
SELECT COUNT(id) FROM proposals;
-- Draft
SELECT COUNT(id) FROM proposals WHERE status = 'draft';
```
```json
{ "rate": 0.22, "total_abandoned": 4 }
```

#### /api/metrics/edit-activity
*Proposal edit counts by team/author (inferred from status history).*
**SQL Query:**
```sql
SELECT p.id as proposal_id, COUNT(psh.id) as edit_count 
FROM proposal_status_history psh 
JOIN proposals p ON psh.proposal_id = p.id 
GROUP BY p.id 
ORDER BY edit_count DESC;
```
```json
{
  "authors": ["Proposal 12345678"],
  "edit_counts": [53]
}
```

#### /api/metrics/reviewer-activity
*Reviews per team/individual.*
**SQL Query:**
```sql
SELECT r.name as reviewer, COUNT(pr.id) as reviews 
FROM proposal_peer_reviews pr 
JOIN users r ON pr.reviewer_id = r.id 
JOIN proposals p ON pr.proposal_id = p.id 
GROUP BY r.name 
ORDER BY reviews DESC;
```
```json
{
  "reviewers": ["ReviewerA", "ReviewerB"],
  "reviews": [19, 2]
}
```

---
### Edge Contract Cases
- **Numbers always returned:** Use 0 for numeric results if empty, never null.
- **Arrays always returned:** Use empty arrays, never null or undefined.
- **Top-level keys always present:** Never omit the documented keys from the payload.

---
## 📚 Knowledge Metrics

### 7. /api/metrics/knowledge-cards
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

---
### 8. /api/metrics/knowledge-cards-history
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

---
### 9. /api/metrics/reference
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

---
### 10. /api/metrics/reference-usage
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

---
### 11. /api/metrics/reference-issue
**Description:** Bad/missing references (un-ingested, errors) by type/team.
**Questions Answered:** Where does reference integrity break down?
```json
{
  "error_types": ["NotIngested", "Error"],
  "counts": [3, 1]
}
```

---
### Additional Advanced Knowledge Metrics

#### /api/metrics/card-edit-frequency
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

#### /api/metrics/card-impact-score
*Aggregate views or usages for each card.*
```json
{
  "card_ids": ["kc-1", "kc-2"],
  "impact_scores": [36, 7]
}
```

#### /api/metrics/knowledge-silos
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

