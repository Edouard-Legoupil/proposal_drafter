# Research Report: Proposal Drafter Implementation

**Version:** 1.0  
**Date:** 2025-05-13  
**Input:** Feature specification from `/specs/001-proposal_drafter/spec.md`  
**Purpose:** Resolve unknowns identified during Technical Context analysis

---

## Executive Summary

This research document addresses the NEEDS CLARIFICATION items identified during the planning phase for the Proposal Drafter system. The Proposal Drafter is a production-ready agentic AI system for UN agencies and NGOs, with all core features already implemented. This research focuses on defining performance goals, operational constraints, and scale expectations for optimal production deployment.

---

## Resolved Unknowns

### 1. Performance Goals

**Unknown:** Target response times and throughput not specified in current spec  
**Research Task:** Determine target performance metrics for Proposal Drafter  
**Status:** ✅ RESOLVED  

#### Decision

Based on the system's use case (proposal generation for UN agencies/NGOs) and the technology stack, the following performance goals are recommended:

- **API Response Time (p95):** < 500ms for simple requests, < 2000ms for complex generation requests
- **Proposal Generation Time:** < 5 minutes for full proposal (all sections)
- **Section Generation Time:** < 30 seconds per section
- **Throughput:** 100 concurrent proposal generation sessions
- **Concurrent Users:** 500+ simultaneous active users
- **Database Query Time (p95):** < 100ms for simple queries, < 500ms for complex joins with vector search

#### Rationale

1. **User Experience:** Proposal generation is the core feature. Users expect near-instant feedback for simple operations and reasonable wait times for complex AI-generated content.

2. **LLM Constraints:** Azure OpenAI GPT-4 has inherent latency. The 5-minute target for full proposal generation accounts for:
   - LLM response times (10-60 seconds per call depending on complexity)
   - Multiple sections being generated sequentially
   - Database lookups and knowledge card retrieval
   - Document assembly and formatting

3. **UN/NGO Context:** These organizations typically have moderate user bases but require reliable performance. 500+ concurrent users covers most deployment scenarios.

4. **Vector Search:** pgvector similarity searches on 1536-dimensional embeddings typically complete in 50-200ms for well-indexed tables.

#### Alternatives Considered

1. **More Aggressive Targets (p95 < 100ms API):** Rejected - Not feasible given LLM dependencies and the complexity of proposal generation.

2. **Higher Throughput (1000+ concurrent):** Rejected - Would require significant infrastructure investment (more GPUs, larger database instances) that may not be justified for typical UN/NGO use cases.

3. **Faster Generation (< 2 minutes):** Rejected - Would compromise quality and completeness of generated proposals.

---

### 2. Operational Constraints

**Unknown:** Resource limits and operational constraints not specified in current spec  
**Research Task:** Identify resource limits and operational constraints (memory, CPU, storage, network)  
**Status:** ✅ RESOLVED  

#### Decision

The following operational constraints are recommended based on production deployment experience with similar systems:

**Compute Resources:**
- **Backend (FastAPI):** 4 vCPUs, 8GB RAM per instance
- **Frontend:** 2 vCPUs, 4GB RAM per instance
- **Database (PostgreSQL + pgvector):** 8 vCPUs, 32GB RAM, 100GB SSD storage
- **Redis:** 2 vCPUs, 4GB RAM, 10GB SSD storage

**Storage Requirements:**
- **Database:** 100GB initial, scalable based on usage
- **Document Storage:** 1TB for generated documents (Word, PDF, Excel)
- **Logs:** 50GB with 30-day retention
- **Backups:** 200GB (compressed database + document backups)

**Network:**
- **Bandwidth:** 1Gbps minimum
- **Latency:** < 50ms to LLM providers (Azure OpenAI/Google Vertex AI)
- **API Rate Limits:** 1000 requests/minute per user (configurable)

**Session Management:**
- **Session Timeout:** 8 hours of inactivity
- **Max Session Size:** 10MB per session (form data, drafts, metadata)
- **Concurrent Sessions:** 10,000 maximum

#### Rationale

1. **Backend Resources:** FastAPI with CrewAI orchestrating multiple agents requires sufficient memory for concurrent LLM context management. 8GB allows for ~100 concurrent generation sessions.

2. **Database Resources:** PostgreSQL with pgvector for 1536-dimensional embeddings requires significant memory for efficient vector search. 32GB supports millions of knowledge cards.

3. **Storage:** Proposals can be large documents (50-500 pages). 1TB allows for ~10,000 large proposals with versions.

4. **Network:** 1Gbps handles concurrent document uploads/downloads and API traffic. Low latency to LLM providers is critical for user experience.

5. **Session Constraints:** 8-hour timeout balances user convenience with resource management. 10MB session size limit prevents memory exhaustion.

#### Alternatives Considered

1. **Smaller Instances:** Rejected - Would limit concurrent users and degrade performance under load.

2. **No Storage Limits:** Rejected - Unbounded storage growth is unsustainable for production systems.

3. **Longer Session Timeout:** Rejected - Increases resource usage and security risk (stale sessions).

---

### 3. Scale/Scope

**Unknown:** Expected user base and concurrent session limits not specified in current spec  
**Research Task:** Determine expected user base and concurrent session limits  
**Status:** ✅ RESOLVED  

#### Decision

Based on typical UN agency and NGO deployment scenarios:

**Deployment Scales:**

| Deployment Type | Users | Concurrent Sessions | Proposals/Month | Storage/Month |
|----------------|-------|-------------------|----------------|---------------|
| Small (Single Team) | 10-50 | 5-20 | 20-100 | 1-5 GB |
| Medium (Department) | 50-200 | 20-100 | 100-500 | 5-25 GB |
| Large (Organization) | 200-1000 | 100-500 | 500-2500 | 25-125 GB |
| Enterprise (Multi-Org) | 1000+ | 500+ | 2500+ | 125+ GB |

**Recommended Initial Configuration:** Medium deployment (200 users, 100 concurrent sessions)

**Growth Projections:**
- Year 1: 200-500 users, 500-1000 proposals
- Year 2: 500-1000 users, 2000-5000 proposals
- Year 3: 1000+ users, 5000+ proposals

**Scaling Strategy:**
- **Horizontal Scaling:** Backend and frontend can scale horizontally with load balancers
- **Database Scaling:** PostgreSQL read replicas for query scaling, connection pooling
- **Redis Cluster:** Horizontal scaling for session storage
- **LLM Rate Limiting:** Per-user and per-organization rate limits to manage costs

#### Rationale

1. **UN/NGO Context:** Most UN agencies and NGOs have 10-1000 employees in relevant departments (program management, fundraising, partnerships).

2. **Proposal Volume:** Each organization typically creates 1-10 proposals per month per user, depending on their funding cycle.

3. **Seasonal Variation:** Proposal generation often spikes during funding cycles (quarterly, annually). The system should handle 2-3x normal load during peaks.

4. **Storage Growth:** Average proposal is ~1-5MB (Word doc). With versions and metadata, average 5-10MB per proposal.

#### Alternatives Considered

1. **Optimistic Projections:** Rejected - Overestimating initial user base leads to overspending on infrastructure.

2. **No Scaling Plan:** Rejected - System must be designed for growth from day one.

3. **Single Monolithic Deployment:** Rejected - Microservices architecture (or at least service separation) allows for independent scaling.

---

## Technology-Specific Best Practices

### FastAPI Production Deployment

**Decision:** Gunicorn with Uvicorn workers  
**Rationale:** Gunicorn provides production-ready process management while Uvicorn workers handle ASGI (WebSocket/SSE) support.  
**Configuration:**
```bash
# Recommended production setup
workers = (2 * CPU_Cores) + 1  # e.g., 5 workers for 4 vCPU
gunicorn -w 5 -k uvicorn.workers.UvicornWorker main:app
```
**Alternatives Considered:**
- Uvicorn alone: Not recommended for production (no process management)
- Daphne: ASGI server but less mature than Uvicorn

---

### React + Vite Optimization

**Decision:** Vite for fast builds and HMR  
**Rationale:** Vite provides:
- Instant server start (no bundling in development)
- Lightning-fast HMR (Hot Module Replacement)
- Optimized production builds (Rollup-based)
- Out-of-the-box TypeScript, JSX, CSS support
- Plugin ecosystem for React, ESLint, Prettier

**Configuration:**
```javascript
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8502',
      '/sse': {
        target: 'http://localhost:8502',
        ws: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
```
**Alternatives Considered:**
- Create React App: Slower builds, no HMR, being deprecated
- Next.js: Overkill for this use case (SSR not needed)

---

### PostgreSQL with pgvector

**Decision:** pgvector extension for vector embeddings  
**Rationale:**
- Native PostgreSQL extension, no external dependencies
- Efficient approximate nearest neighbor search using HNSW
- Supports filtering with vector search (e.g., find similar knowledge cards for specific donor)
- ACID compliant with PostgreSQL transactions
- No separate vector database to manage

**Configuration:**
```sql
-- Enable extension
CREATE EXTENSION vector;

-- Create index for knowledge cards
CREATE INDEX idx_knowledge_card_embedding 
ON knowledge_cards 
USING hnsw (embedding vector_l2_ops) 
WITH (m = 16, ef_construction = 64);

-- Query example
SELECT * FROM knowledge_cards 
ORDER BY embedding <=> '[0.1, 0.2, ...]' 
LIMIT 10;
```
**Alternatives Considered:**
- FAISS: Requires separate service, not ACID compliant
- Weaviate: External service, adds complexity
- Pinecone: Managed service, vendor lock-in, cost

---

### Redis for Session Management

**Decision:** Redis 7+ with HTTP-only cookies  
**Rationale:**
- In-memory data store for low-latency session access
- Persistence options (RDB/AOF) for durability
- Pub/Sub support for real-time features (SSE)
- HTTP-only cookies prevent XSS-based session hijacking
- Secure flag ensures cookies only sent over HTTPS
- SameSite=Strict/Lax prevents CSRF

**Configuration:**
```python
# FastAPI Redis session configuration
from fastapi_sessions.redis import RedisSessionInterface

redis = Redis(host='localhost', port=6379, db=0)
session_interface = RedisSessionInterface(redis, secret=SECRET_KEY, cookie_name='session', max_age=8*60*60)

# Cookie settings
cookie_params = {
    'httponly': True,
    'secure': True,
    'samesite': 'lax',
    'max_age': 8 * 60 * 60  # 8 hours
}
```
**Alternatives Considered:**
- Database-backed sessions: Slower, adds database load
- File-based sessions: Not scalable, not suitable for distributed deployments

---

## Security Considerations

### Authentication & Authorization

**Best Practices Identified:**
1. **JWT Token Expiry:** Access tokens: 15 minutes, Refresh tokens: 7 days
2. **Token Storage:** HTTP-only cookies (not localStorage)
3. **Password Policy:** Minimum 12 characters, complexity requirements
4. **Rate Limiting:** 100 requests/minute per IP, 1000/minute per authenticated user
5. **Session Invalidation:** On password change, token revocation

### Data Protection

**Best Practices Identified:**
1. **Input Validation:** Pydantic models for all API inputs
2. **Output Encoding:** Template auto-escaping, explicit encoding for dynamic content
3. **Secrets Management:** Environment variables, Azure Key Vault/Google Secret Manager for production
4. **Encryption:** TLS 1.2+ for all communications, AES-256 for data at rest
5. **Audit Logging:** All sensitive operations logged with user ID, timestamp, IP

### LLM Security

**Best Practices Identified:**
1. **Prompt Engineering:** Structured prompts with explicit boundaries and instructions
2. **Content Filtering:** Pre-prompt and post-prompt filtering for sensitive data
3. **Output Validation:** JSON schema validation, repair mechanisms for malformed output
4. **Rate Limiting:** Per-user LLM call limits to manage costs and prevent abuse
5. **Grounding:** Always include relevant knowledge cards in LLM context to minimize hallucinations

---

## Performance Optimization Recommendations

### Backend

1. **Database Connection Pooling:** Use asyncpg or SQLAlchemy with connection pooling
2. **Caching:** Cache frequent queries (templates, knowledge cards metadata)
3. **Background Tasks:** Offload long-running operations (proposal generation, document export) to Celery or background threads
4. **Compression:** Enable GZIP/Brotli compression for API responses

### Frontend

1. **Code Splitting:** Lazy load large components and routes
2. **Bundle Optimization:** Analyze and optimize bundle size with Rollup/Vite
3. **Image Optimization:** Compress and lazy load images
4. **Caching:** Implement service worker for offline capability and caching

### Database

1. **Indexing:** Ensure proper indexes on frequently queried columns
2. **Query Optimization:** Use EXPLAIN ANALYZE to identify slow queries
3. **Vector Search:** Use appropriate HNSW parameters (m, ef_construction, ef_search)
4. **Partitioning:** Consider table partitioning for large tables (proposals, knowledge_cards)

---

## Infrastructure Recommendations

### Development Environment

- **Docker Compose:** Local development with all services (PostgreSQL, Redis, FastAPI, React)
- **Hot Reload:** FastAPI --reload and Vite HMR for rapid development
- **Test Data:** Seed database with realistic test data

### Staging Environment

- **Mirror of Production:** Same configuration as production but smaller scale
- **Test Load:** Simulate production load to identify bottlenecks
- **Security Testing:** Penetration testing, vulnerability scanning

### Production Environment

- **Containerization:** Docker containers for all services
- **Orchestration:** Kubernetes or Docker Compose in production
- **Monitoring:** Prometheus + Grafana for metrics, ELK for logging
- **CI/CD:** Automated testing and deployment pipeline

---

## Cost Considerations

### LLM Costs

- **Azure OpenAI GPT-4:** ~$0.03-$0.06 per 1K tokens (input + output)
- **Average Proposal:** ~50K tokens (prompt + generation)
- **Cost per Proposal:** ~$1.50-$3.00
- **Monthly Cost (1000 proposals):** ~$1,500-$3,000

### Infrastructure Costs

| Service | Small | Medium | Large |
|---------|-------|--------|-------|
| Compute (Backend) | $50/mo | $200/mo | $500/mo |
| Compute (Frontend) | $25/mo | $100/mo | $250/mo |
| Database | $100/mo | $300/mo | $800/mo |
| Redis | $25/mo | $50/mo | $100/mo |
| Storage | $50/mo | $150/mo | $300/mo |
| **Total** | **$250/mo** | **$800/mo** | **$2,000/mo** |

### Optimization Opportunities

1. **LLM Caching:** Cache frequent LLM responses (knowledge card generation for common topics)
2. **Batch Processing:** Generate multiple proposals in batch to reduce overhead
3. **Model Selection:** Use smaller models (GPT-3.5) for less critical sections
4. **Rate Limiting:** Prevent abuse and manage costs

---

*Generated by `/speckit.architecture-guard.governed-plan` workflow - Phase 0 Research*