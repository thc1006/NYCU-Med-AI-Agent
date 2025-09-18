# Taiwan Medical AI Agent - Architecture Documentation

## Overview

This directory contains comprehensive architecture documentation for the Taiwan Medical AI Agent, a safety-first medical assistant system designed specifically for Taiwan's healthcare environment with Traditional Chinese localization and PDPA compliance.

## Architecture Documents

### 1. System Architecture
- **[High-Level Architecture](system/high-level-architecture.md)**: Overall system design, component diagrams, and architectural principles
- **Key Features**: FastAPI backend, microservices architecture, Taiwan emergency protocol integration

### 2. API Architecture
- **[API Architecture](api/api-architecture.md)**: RESTful API design, endpoint specifications, and error handling
- **[OpenAPI Specification](api/openapi-spec.yaml)**: Complete API contract with Taiwan localization
- **Key Features**: zh-TW responses, emergency contact integration, medical disclaimers

### 3. Data Architecture
- **[Data Architecture](data/data-architecture.md)**: Data models, storage patterns, and PDPA compliance
- **Key Features**: Privacy-first design, minimal data retention, Traditional Chinese support

### 4. Security & Privacy
- **[Security Architecture](security/security-architecture.md)**: Comprehensive security framework with PDPA compliance
- **Key Features**: PII masking, encryption, audit logging, medical safety controls

### 5. Medical Safety
- **[Medical Safety Architecture](medical/medical-safety-architecture.md)**: Emergency protocols and medical guidance safety
- **Key Features**: Taiwan emergency services (119/112), non-diagnostic constraints, safety validation

### 6. Taiwan Localization
- **[Taiwan Localization Architecture](localization/taiwan-localization-architecture.md)**: Cultural and linguistic adaptations
- **Key Features**: Traditional Chinese, Taiwan healthcare system, regional considerations

### 7. LLM Interface
- **[LLM Interface Architecture](llm/llm-interface-architecture.md)**: Modular, pluggable LLM integration
- **Key Features**: Provider-agnostic design, medical safety validation, fallback mechanisms

### 8. Testing Architecture
- **[Testing Architecture](testing/testing-architecture.md)**: Comprehensive testing strategy with TDD approach
- **Key Features**: pytest framework, RESpx mocking, medical safety testing

### 9. Scalability & Performance
- **[Scalability Architecture](scalability/scalability-architecture.md)**: Performance optimization and scaling strategies
- **Key Features**: Caching, load balancing, async operations, monitoring

### 10. Deployment & Infrastructure
- **[Deployment Architecture](deployment/deployment-architecture.md)**: Infrastructure as code and deployment strategies
- **Key Features**: Containerization, cloud deployment, monitoring, backup strategies

### 11. Architecture Validation
- **[Architecture Validation](validation/architecture-validation.md)**: Validation framework and decision tracking
- **Key Features**: Automated validation, ADR tracking, compliance monitoring

## Core Architectural Principles

### 1. Safety-First Medical Design
- **Emergency Override**: Critical symptoms trigger immediate emergency protocols
- **Non-Diagnostic**: System provides guidance, never diagnoses
- **Professional Referral**: All responses direct to qualified medical professionals
- **Fail-Safe Defaults**: System defaults to emergency guidance when uncertain

### 2. Taiwan Healthcare Integration
- **Local Emergency Services**: Integration with 119/112 emergency systems
- **NHIA Integration**: Taiwan National Health Insurance system awareness
- **Cultural Sensitivity**: Appropriate communication for Taiwan medical culture
- **Regulatory Compliance**: Adherence to Taiwan medical practice standards

### 3. Privacy by Design (PDPA Compliance)
- **Data Minimization**: Collect only essential information
- **PII Protection**: Automatic masking and anonymization
- **User Rights**: Support for PDPA data subject rights
- **Audit Compliance**: Comprehensive logging for regulatory compliance

### 4. Traditional Chinese Localization
- **Language Consistency**: All interfaces and responses in zh-TW
- **Medical Terminology**: Taiwan-specific medical terms and conventions
- **Cultural Context**: Appropriate communication styles and cultural considerations
- **Regional Variations**: Support for Taiwan's linguistic diversity

## Architecture Decision Records (ADRs)

### Key Decisions
1. **ADR-001**: FastAPI Framework Selection - High performance, type safety
2. **ADR-002**: Google Places API for Hospital Search - Comprehensive coverage, zh-TW support
3. **ADR-003**: Hybrid Rule-Based + LLM Approach - Safety with enhanced responses
4. **ADR-004**: PDPA-First Privacy Architecture - Legal compliance, user trust

## Technology Stack

### Backend Framework
- **FastAPI**: High-performance, type-safe API framework
- **Python 3.11**: Latest stable Python with enhanced features
- **Pydantic**: Data validation and serialization
- **httpx**: Async HTTP client for external APIs

### External Integrations
- **Google Places API (New)**: Hospital search with zh-TW localization
- **Google Geocoding API**: Address to coordinates conversion
- **Anthropic Claude**: LLM for enhanced medical guidance
- **IP Geolocation**: Automatic location detection

### Data & Caching
- **Redis**: Session data and response caching
- **PostgreSQL**: Audit logs and configuration data
- **JSON/YAML**: Static configuration and NHIA registry

### Testing & Quality
- **pytest**: Comprehensive test framework
- **RESpx**: HTTP mocking for external API testing
- **TestClient**: FastAPI integration testing
- **Coverage**: Code coverage reporting

## Security Framework

### Authentication & Authorization
- **API Key Authentication**: Secure service access
- **Rate Limiting**: Abuse prevention and cost control
- **Input Validation**: Comprehensive request validation
- **Output Sanitization**: Safe response formatting

### Data Protection
- **Encryption**: AES-256 for data at rest, TLS 1.3 for transit
- **PII Anonymization**: Hash/mask personal information
- **Audit Logging**: Complete activity tracking (PDPA compliant)
- **Access Controls**: Role-based permissions

### Medical Safety Controls
- **Emergency Override**: Critical symptoms bypass normal processing
- **Disclaimer Enforcement**: Mandatory medical disclaimers
- **Response Validation**: Safety checks on all medical advice
- **Fallback Mechanisms**: Rule-based backup for LLM failures

## Deployment Architecture

### Containerization
- **Docker**: Application containerization
- **Multi-stage Builds**: Optimized production images
- **Health Checks**: Container monitoring
- **Security Hardening**: Non-root user, minimal base images

### Infrastructure Options
- **Kubernetes**: Container orchestration for production
- **Cloud Run**: Serverless container platform
- **Traditional VPS**: Virtual private server deployment
- **Docker Compose**: Local development environment

### Monitoring & Observability
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and alerting
- **ELK Stack**: Log aggregation and analysis
- **Health Endpoints**: Application health monitoring

## Development Workflow

### Test-Driven Development (TDD)
1. **Write Tests First**: All features start with failing tests
2. **Minimal Implementation**: Write just enough code to pass tests
3. **Refactor**: Improve code while maintaining test coverage
4. **Repeat**: Iterate with confidence

### Medical Safety Testing
- **Emergency Scenario Testing**: Validate critical symptom handling
- **Response Safety Validation**: Ensure non-diagnostic outputs
- **Disclaimer Compliance**: Verify medical disclaimer presence
- **Fallback Testing**: Validate backup mechanisms

### Integration Testing
- **External API Mocking**: RESpx for Google APIs
- **End-to-End Scenarios**: Complete user journey testing
- **Error Handling**: Comprehensive error scenario coverage
- **Performance Testing**: Response time and throughput validation

## Quality Assurance

### Code Quality
- **Type Hints**: Comprehensive type annotations
- **Linting**: Automated code style checking
- **Documentation**: Inline and architectural documentation
- **Code Review**: Peer review for all changes

### Medical Safety Quality
- **Safety Review**: Medical expert validation of responses
- **Emergency Protocol Testing**: Verification of emergency handling
- **Compliance Auditing**: PDPA and medical regulation compliance
- **Cultural Validation**: Taiwan localization review

### Performance Quality
- **Response Time Targets**: < 500ms for triage, < 1s for hospital search
- **Caching Strategy**: Intelligent caching for improved performance
- **Load Testing**: Capacity planning and bottleneck identification
- **Resource Optimization**: Memory and CPU usage optimization

## Getting Started

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Google Cloud Account (for Places/Geocoding APIs)
- Redis instance
- Anthropic API key (optional, for LLM features)

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys and configuration

# Start development services
docker-compose up -d redis

# Run tests
pytest

# Start development server
uvicorn app.main:app --reload
```

### Configuration
Key environment variables:
- `GOOGLE_PLACES_API_KEY`: Google Places API access
- `GOOGLE_GEOCODING_API_KEY`: Google Geocoding API access
- `ANTHROPIC_API_KEY`: Anthropic Claude API (optional)
- `REDIS_URL`: Redis connection string
- `ENVIRONMENT`: deployment environment (development/staging/production)

## Contributing

### Architecture Changes
1. **Document First**: Create or update ADR for significant decisions
2. **Security Review**: All changes must pass security validation
3. **Medical Safety**: Changes affecting medical logic require medical review
4. **Testing**: Comprehensive tests for all architectural changes

### Code Standards
- Follow Python PEP 8 style guidelines
- Maintain 90%+ test coverage
- Include type hints for all functions
- Document public APIs with docstrings

### Medical Content Standards
- All medical content must be reviewed by qualified medical professionals
- Responses must include appropriate disclaimers
- Emergency scenarios must be tested thoroughly
- Cultural sensitivity must be maintained for Taiwan context

## Support and Maintenance

### Monitoring
- **Health Checks**: Automated system health monitoring
- **Performance Metrics**: Response time and error rate tracking
- **Security Alerts**: Automated security incident detection
- **Compliance Monitoring**: PDPA and medical regulation compliance tracking

### Backup and Recovery
- **Database Backups**: Automated daily backups with point-in-time recovery
- **Configuration Backup**: Version-controlled configuration management
- **Disaster Recovery**: Documented recovery procedures
- **Business Continuity**: Failover mechanisms for critical services

### Updates and Maintenance
- **Security Updates**: Regular dependency and security updates
- **Medical Content Review**: Periodic review of medical guidance accuracy
- **Performance Optimization**: Ongoing performance monitoring and optimization
- **Compliance Review**: Regular PDPA and regulatory compliance audits

---

This architecture provides a solid foundation for building a safe, reliable, and culturally appropriate medical AI assistant for Taiwan's healthcare environment. The comprehensive documentation ensures maintainability and facilitates future enhancements while maintaining the highest standards of medical safety and regulatory compliance.