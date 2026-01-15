# Analytics Backend API Expansion Proposal

This proposal enumerates endpoints necessary for full-featured analytics and dashboard capabilities in the metrics system:

---

## 1. Proposal/Project Metrics
- **GET /api/metrics/proposals?filter_by=user/team/all&status=...&donor=...&outcome=...&date_start=...&date_end=...**
  - Returns: List of proposals matching detailed filters
  - Supports: Pagination, sorting, field selection

- **GET /api/metrics/proposal-trends?group_by=day/week/month&date_start=...&date_end=...**
  - Returns: Time-series submission/completion counts

---

## 2. Knowledge Card Metrics
- **GET /api/metrics/knowledge-cards?created_by=...&referenced_in_proposal=bool&date_start=...&date_end=...**
  - Returns: Knowledge Card stats (created, updated, referenced, flagged, AI-generated vs manual)
- **GET /api/metrics/knowledge-card-trends?...**
  - Returns: Time-series for Knowledge Card creation/reference

---

## 3. AI System Metrics
- **GET /api/metrics/ai-usage?group_by=day/week/month&date_start=...&date_end=...**
  - Returns: Completions, error rate, moderation flags, cost

---

## 4. Infrastructure & Health Metrics
- **GET /api/metrics/app-health?date_start=...&date_end=...**
  - Returns: uptime, API latency, error %, outage events
- **GET /api/metrics/db-performance?date_start=...&date_end=...**
  - Returns: slow query, connection stats

---

## 5. Review/Workflow Metrics
- **GET /api/metrics/review-performance?reviewer=...&date_start=...&date_end=...**
  - Returns: review duration, approval rates, throughput
---

## 6. Universal Raw Event Table
- **GET /api/events?type=proposal|knowledge_card|review|ai_call&filter=...**
  - Returns: fully queryable, paginated, sortable event table

---

# Notes
- All endpoints support date ranges, multi-field facets, pagination, sorting
- All endpoints return count, time-series, and row-level data as appropriate
- User, team, donor, outcome, status, field_context included where applicable

---
