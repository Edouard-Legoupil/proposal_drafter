# Runbook / Support Procedures

A guide for handling common support incidents, scaling operations, and database backup/restore for this application.

---

## 1. Azure OpenAI Service Unavailable

**Symptoms:**  
- Errors in AI-generated proposals, chat, or knowledge cards
- API calls to OpenAI service fail (timeouts, 500, quota, auth errors)

**Immediate Response:**
1. **Confirm Service Status**
   - Visit [Azure Status Page](https://status.azure.com/en-us/status) → "AI + Machine Learning"
   - Check [OpenAI Resource Health](https://portal.azure.com) in Azure Portal

2. **Workaround / Failover**
   - If possible, reroute traffic to a backup LLM endpoint (e.g., use Azure Foundry or local inference)
   - Communicate incident and activate manual workflows if necessary.

3. **Log and Notify**
   - Record the incident in your incident tracking system.
   - Notify stakeholders and instruct end-users to avoid relying on AI content until stable.

4. **Restart App Services**
   - Go to Azure Portal → App Service → Restart if cascading failures occur.

5. **Post-Incident**
   - Confirm service restoration.
   - Review logs for failed calls (`/logs/`, App Insights).
   - Re-enable full user workflows when stable.

---

## 2. Scaling Up App Service During Usage Spikes

**Symptoms:**  
- Slow UI, delayed responses, timeouts, HTTP 503/429 errors.

**Step-by-Step:**
1. **Monitor Usage**
   - In Azure Portal: Go to **App Service → Monitoring → Metrics**
   - Check CPU, memory, requests, HTTP queue

2. **Manual Scale Up**
   - Azure Portal → App Service → "Scale Up (App Service Plan)"
     - Select next pricing tier (S2, S3, P1v3, etc.)
   - Or "Scale Out (Increase Instance Count)"
     - Go to "Scale Out (App Service Plan)" → Increase "Instance count" (e.g., to 3+)

3. **Auto-Scale Configuration (Recommended)**
   - Azure Portal → "Scale Out (App Service Plan)" → Set "Custom autoscale"
     - Configure metric rules (CPU > 70%, requests > limit, etc.)
     - Set minimum and maximum instance count

4. **Validate**
   - After scaling, verify app responsiveness
   - Confirm scaling event in Activity Log

5. **Rollback**
   - Scale down excess resources after spike subsides.

---

## 3. PostgreSQL Backup and Restore Procedures

### Backup (Azure Database for PostgreSQL)

**Automated Backups**
- Azure handles daily automated backups (retention: 7-35 days, depending on tier)

**Manual Snapshot**
1. **Via Azure Portal**
   - Go to Azure Database for PostgreSQL server.
   - Under "Backups", confirm latest available.
   - Create a manual backup:  
     - Connect using `pg_dump` (from local, VM, or cloud shell):

       ```sh
       pg_dump --host=<hostname> --username=<admin> --port=5432 <dbname> > db-backup-YYYYMMDD.sql
       ```

   - Store backup in secure cloud storage (e.g. Azure Blob, GitHub secrets).

2. **Automated Script/Job Example**
   - Use a scheduled job (Azure Automation, Logic App, GitHub Actions):

     ```sh
     pg_dump -h <host> -U <user> <dbname> | gzip > db-backup-$(date +%F).sql.gz
     ```

### Restore

1. **Restore from Automated Azure Backup**
   - In Azure Portal, go to PostgreSQL server.
   - Use "Restore" to create a new server from backup (point-in-time restore).
   - Update app configuration (`DATABASE_URL`) to point to new server if needed.

2. **Restore from Manual Dump**
   - On a new or clean PostgreSQL server:

     ```sh
     psql --host=<hostname> --username=<admin> --port=5432 <dbname> < db-backup-YYYYMMDD.sql
     ```
   - Confirm restore (`SELECT COUNT(*) ...` on required tables).

### Validation
- Test basic app workflows/login
- Check record counts and recent entries
- Monitor logs for errors

### Schedule
- Backups should run DAILY or immediately before risky upgrades/server maintenance.
- Retain at least 7+ recent backups in secure location.

---

## References & More Resources

- [Azure OpenAI - Monitoring & Troubleshooting](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Scaling App Service](https://learn.microsoft.com/en-us/azure/app-service/manage-scale-up)
- [PostgreSQL Backup/Restore](https://learn.microsoft.com/en-us/azure/postgresql/single-server/concepts-backup)
