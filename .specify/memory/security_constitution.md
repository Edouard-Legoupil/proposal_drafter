# Proposal Drafter Security Constitution

**Version:** 1.0
**Last Updated:** 2025
**Status:** Active
**Compliance Framework:** ISO 27001, OWASP Top 10

---

## 1. Trust Boundaries

### 1.1 Entry Points
- **Web UI (React)**: Primary user interface accessible via HTTPS
- **REST API (FastAPI)**: Backend services with OAuth 2.0 authentication
- **File Uploads**: Document upload functionality with strict validation

### 1.2 Internal Isolation Requirements
- **PostgreSQL Database**: Must remain completely isolated from public web access
- **LLM Services (Azure OpenAI/Vertex AI)**: Internal API access only
- **Internal APIs**: Backend services not directly exposed to internet

### 1.3 Network Architecture
- **Public Zone**: Web UI, API Gateway
- **Private Zone**: Database, LLM Services, Internal APIs
- **DMZ**: Authentication services, file processing

---

## 2. Authentication & Authorization Standards

### 2.1 Authentication Mechanism
- **Primary**: OAuth 2.0 with Azure EntraID integration
- **Token Standard**: JWT (JSON Web Tokens) with HS256 signing
- **Session Management**: Secure HTTP-only cookies with SameSite=Lax

### 2.2 Multi-Factor Authentication
- **Requirement**: MFA required for ALL user actions
- **Implementation**: Azure MFA integration
- **Step-up Auth**: Additional verification for sensitive operations

### 2.3 Authorization Framework
- **Model**: Attribute-Based Access Control (ABAC)
- **Implementation**: Policy-based authorization engine
- **Attributes**: User roles, resource ownership, context attributes

### 2.4 Role Definitions
```
- admin: Full system access
- knowledge_manager: Knowledge card management
- proposal_writer: Proposal creation/editing
- reviewer: Review and approval workflows
- donor_focal: Donor-specific access
- qa_lead: Quality assurance oversight
```

---

## 3. Data Isolation & Privacy Rules

### 3.1 Single-Tenant Architecture
- **Model**: Single tenant system (no multi-tenancy requirements)
- **Data Separation**: Logical separation by user/team ownership

### 3.2 Sensitive Data Handling
- **Primary Concern**: Proposal content (confidential project information)
- **Storage**: Encrypted at rest (Azure Storage Service Encryption)
- **Transmission**: TLS 1.2+ for all communications

### 3.3 Data Retention & Disposal
- **Retention Period**: 7 years for completed proposals
- **Disposal Method**: Secure deletion with verification
- **Audit Trail**: All disposal actions logged

---

## 4. Secrets Management Policy

### 4.1 Storage & Injection
- **Primary**: Azure Key Vault for all secrets
- **Access Pattern**: Runtime retrieval via managed identity
- **Rotation**: Automatic secret rotation every 90 days

### 4.2 Prohibited Practices
- **No Hardcoded Secrets**: Absolute prohibition in code
- **No Environment Variables in Code**: Use configuration management
- **No Shared Credentials**: Individual service principals

### 4.3 Secret Types
```
- Database credentials
- API keys (Azure OpenAI, Vertex AI)
- OAuth client secrets
- Encryption keys
- Service account credentials
```

---

## 5. Secure-by-Design Patterns

### 5.1 Input Validation
- **Framework**: Pydantic models for all API requests
- **Validation**: Strict type checking and constraint validation
- **Sanitization**: HTML/JS injection prevention

### 5.2 Database Security
- **ORM**: SQLAlchemy with parameterized queries
- **Connection Pooling**: Secure connection management
- **Audit Logging**: All database access logged

### 5.3 API Security
- **Rate Limiting**: Per-user request throttling
- **CORS**: Strict origin policies
- **CSRF Protection**: Anti-CSRF tokens for state-changing operations

### 5.4 File Handling
- **Upload Validation**: File type, size, and content verification
- **Virus Scanning**: Automated malware detection
- **Sandbox Processing**: Isolated environment for file processing

---

## 6. API & Integration Security

### 6.1 External Communication
- **TLS Requirements**: TLS 1.2+ for all external connections
- **Certificate Validation**: Strict certificate pinning
- **Timeout Policies**: Short connection timeouts

### 6.2 Third-Party Integrations
- **OAuth Flows**: PKCE for public clients
- **API Keys**: Short-lived tokens with limited scope
- **Webhooks**: HMAC signature verification

### 6.3 LLM Security
- **Prompt Injection Prevention**: Structured prompts with clear boundaries
- **Output Validation**: JSON schema validation and repair
- **Content Filtering**: Prohibited content detection
- **Usage Monitoring**: Anomaly detection for LLM calls

---

## 7. Audit, Logging & Monitoring

### 7.1 Security Logging
- **Events**: All authentication, authorization, and data access
- **Format**: Structured JSON logs
- **Retention**: 12 months hot storage, 7 years cold storage

### 7.2 Monitoring
- **SIEM Integration**: Azure Sentinel
- **Alerting**: Real-time security event notifications
- **Anomaly Detection**: Machine learning-based pattern recognition

### 7.3 Audit Requirements
- **Access Reviews**: Quarterly access certification
- **Penetration Testing**: Annual third-party assessments
- **Vulnerability Scanning**: Continuous automated scanning

---

## 8. Compliance Mapping

### 8.1 ISO 27001 Controls

**A.5: Information Security Policies**
- Security Constitution as governing document
- Regular review and update cycle

**A.6: Organization of Information Security**
- Defined roles and responsibilities
- Security awareness training

**A.7: Human Resource Security**
- Background checks for privileged access
- Termination procedures

**A.8: Asset Management**
- Inventory of information assets
- Acceptable use policies

**A.9: Access Control**
- ABAC implementation
- MFA requirement
- Privileged access management

**A.10: Cryptography**
- TLS 1.2+ enforcement
- Encryption at rest

**A.11: Physical and Environmental Security**
- Azure data center controls
- Secure workstation policies

**A.12: Operations Security**
- Change management procedures
- Capacity monitoring

**A.13: Communications Security**
- Network segmentation
- Secure API communication

**A.14: System Acquisition, Development and Maintenance**
- Secure development lifecycle
- Code review requirements

**A.15: Supplier Relationships**
- Third-party security assessments
- Contractual security requirements

**A.16: Information Security Incident Management**
- Incident response plan
- Forensic readiness

**A.17: Information Security Aspects of Business Continuity Management**
- Disaster recovery planning
- Backup and restore procedures

**A.18: Compliance**
- Regular compliance audits
- Legal and regulatory monitoring

### 8.2 OWASP Top 10 Mitigations

**A01:2021 – Broken Access Control**
- ABAC implementation
- Regular access reviews

**A02:2021 – Cryptographic Failures**
- TLS 1.2+ enforcement
- Proper key management

**A03:2021 – Injection**
- Parameterized queries
- Input validation

**A04:2021 – Insecure Design**
- Secure design patterns
- Threat modeling

**A05:2021 – Security Misconfiguration**
- Automated configuration management
- Regular security scanning

**A06:2021 – Vulnerable and Outdated Components**
- Dependency monitoring
- Regular updates

**A07:2021 – Identification and Authentication Failures**
- OAuth 2.0 implementation
- MFA requirement

**A08:2021 – Software and Data Integrity Failures**
- Code signing
- Integrity checks

**A09:2021 – Security Logging and Monitoring Failures**
- Comprehensive logging
- SIEM integration

**A10:2021 – Server-Side Request Forgery**
- Input validation
- Network segmentation

---

## 9. Incident Response Plan

### 9.1 Classification
```
- P0: Critical (Immediate action, <1 hour response)
- P1: High (Action within 4 hours)
- P2: Medium (Action within 24 hours)
- P3: Low (Action within 72 hours)
```

### 9.2 Response Team
- **Security Lead**: Primary contact
- **Technical Lead**: Investigation coordination
- **Legal Counsel**: Compliance guidance
- **PR/Communications**: External messaging

### 9.3 Containment Strategies
- **Network Isolation**: Segment affected systems
- **Account Lockdown**: Disable compromised credentials
- **Service Degradation**: Reduce functionality if needed

---

## 10. Security Training & Awareness

### 10.1 Requirements
- **Annual Training**: Mandatory for all developers
- **New Hire Onboarding**: Security orientation
- **Role-Specific**: Additional training for privileged roles

### 10.2 Topics Covered
- Secure coding practices
- Phishing awareness
- Incident reporting procedures
- Compliance requirements

---

## 11. Review & Maintenance

### 11.1 Constitution Review Cycle
- **Quarterly**: Internal review
- **Annual**: Comprehensive audit
- **Trigger-Based**: After major incidents or changes

### 11.2 Change Management
- **Approval**: Security team sign-off required
- **Documentation**: All changes versioned and documented
- **Communication**: Changes communicated to all stakeholders

---

*This Security Constitution establishes the comprehensive security framework for the Proposal Drafter project, aligned with ISO 27001 and OWASP Top 10 requirements for an externally facing PaaS solution in the Design & Build Review Phase.*

**Approvers:**
- Security Lead: [TBD]
- Technical Lead: [TBD]
- Compliance Officer: [TBD]

**Review Cycle:** Quarterly or as needed based on risk assessment.
