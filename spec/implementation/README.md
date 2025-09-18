# Implementation Framework for Medical AI Agent

This directory contains the complete implementation framework for the Taiwan Medical AI Agent, featuring test-driven development, medical safety validation, and Taiwan compliance.

## 📁 Directory Structure

```
spec/implementation/
├── agents/
│   └── spec-task-executor.js         # Main task execution agent
├── templates/
│   ├── fastapi-medical-service.py    # FastAPI service template
│   └── medical-tdd-template.py       # TDD testing template
├── validators/
│   ├── code-quality-validator.js     # Code quality validation
│   └── taiwan-compliance-validator.js # Taiwan compliance validation
├── workflows/
│   ├── tdd-medical-workflow.js       # TDD workflow integration
│   └── fastapi-medical-patterns.py   # Medical patterns and best practices
├── tracking/
│   └── implementation-tracker.js     # Progress tracking and metrics
└── README.md                         # This file
```

## 🚀 Quick Start

### 1. Initialize the Spec Task Executor

```javascript
const SpecTaskExecutor = require('./agents/spec-task-executor');

const executor = new SpecTaskExecutor({
  projectRoot: '/path/to/your/project',
  testFirst: true,
  medicalSafety: true,
  taiwanCompliance: true
});

// Execute a medical AI task
const taskSpec = {
  title: "Implement symptom triage endpoint",
  description: "Create API endpoint for symptom assessment with medical safety",
  type: "api_endpoint",
  requirements: ["Emergency keyword detection", "Medical disclaimers", "zh-TW support"]
};

await executor.executeTask(taskSpec);
```

### 2. Use FastAPI Medical Templates

```python
# Import the medical service template
from spec.implementation.templates.fastapi_medical_service import create_medical_app

# Create your medical AI app
app = create_medical_app({
    "google_api_key": "your_api_key",
    "allowed_origins": ["https://yourdomain.com"]
})

# Run with uvicorn
# uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3. Run TDD Workflow

```javascript
const TDDMedicalWorkflow = require('./workflows/tdd-medical-workflow');

const workflow = new TDDMedicalWorkflow({
  testFramework: 'pytest',
  medicalSafetyRequired: true,
  taiwanComplianceRequired: true
});

await workflow.executeTDDWorkflow(taskSpec);
```

## 🏥 Medical Safety Features

### Emergency Keyword Detection
```python
EMERGENCY_KEYWORDS = [
    "胸痛", "呼吸困難", "意識不清", "劇烈頭痛",
    "大量出血", "嚴重外傷", "中毒", "過敏反應"
]
```

### Medical Disclaimers
All responses include:
- Warning that system provides reference information only
- Guidance to call 119 for emergencies
- Recommendation to consult medical professionals
- Clear statement that system doesn't provide diagnoses

### Privacy Protection (PDPA Compliance)
- PII detection and masking
- Taiwan ID number protection
- Phone number anonymization
- Email address masking
- Audit logging with minimal data exposure

## 🇹🇼 Taiwan Compliance

### Language Support
- Traditional Chinese (zh-TW) throughout
- Simplified Chinese character detection and replacement
- UTF-8 encoding validation
- Proper locale configuration

### Emergency Numbers
```javascript
const TAIWAN_EMERGENCY_NUMBERS = {
  "119": "消防局救護車",
  "110": "警察局",
  "112": "行動電話國際緊急號碼",
  "113": "保護專線",
  "165": "反詐騙諮詢專線"
};
```

### API Localization
- Google Maps API with `language=zh-TW` and `region=TW`
- Taiwan-specific date/time formatting
- Asia/Taipei timezone configuration
- TWD currency support

## 🧪 Test-Driven Development

### Test Structure
```
tests/
├── unit/                    # Unit tests
├── integration/            # Integration tests
├── medical_safety/         # Medical safety tests
├── taiwan_compliance/      # Taiwan compliance tests
└── e2e/                   # End-to-end tests
```

### Medical Safety Tests
```python
def test_emergency_symptoms_trigger_emergency_response(test_client):
    response = test_client.post("/v1/triage", json={
        "symptom_text": "胸痛且呼吸困難"
    })

    data = response.json()
    assert data["level"] == "emergency"
    assert data["should_call_119"] is True
    assert "119" in data["advice"]
```

### Taiwan Compliance Tests
```python
def test_responses_use_traditional_chinese(test_client):
    response = test_client.get("/healthz")
    data = response.json()

    assert data["locale"] == "zh-TW"
    # Check for Traditional Chinese characters
    assert "醫" in str(data) and "医" not in str(data)
```

## 📊 Code Quality Validation

### Automated Checks
- Medical safety compliance
- Taiwan localization validation
- Test coverage (80% minimum)
- Code quality metrics
- Security vulnerability scanning
- PII detection

### Usage
```javascript
const CodeQualityValidator = require('./validators/code-quality-validator');

const validator = new CodeQualityValidator({
  medicalSafetyChecks: true,
  taiwanComplianceChecks: true,
  testCoverageThreshold: 80
});

const report = await validator.validateCodeQuality(['src/**/*.py']);
```

## 📈 Progress Tracking

### Implementation Tracker
```javascript
const ImplementationTracker = require('./tracking/implementation-tracker');

const tracker = new ImplementationTracker();

// Start tracking a task
await tracker.startTask('task-1', taskSpec);

// Update progress
await tracker.updateTaskProgress('task-1', 'testing', {
  status: 'completed',
  metrics: { testCoverage: 85 }
});

// Complete task
await tracker.completeTask('task-1');
```

### Metrics Tracked
- Test coverage percentage
- Code quality scores
- Medical safety compliance
- Taiwan compliance percentage
- Implementation velocity
- Lines of code and test count

## 🔧 Configuration

### Environment Variables
```bash
# Required
GOOGLE_PLACES_API_KEY=your_google_places_api_key
GOOGLE_GEOCODING_API_KEY=your_geocoding_api_key

# Optional
DEFAULT_LANG=zh-TW
REGION=TW
TEST_COVERAGE_THRESHOLD=80
MEDICAL_SAFETY_REQUIRED=true
TAIWAN_COMPLIANCE_REQUIRED=true
```

### Config File Example
```python
# config.py
TAIWAN_CONFIG = {
    "language": "zh-TW",
    "region": "TW",
    "timezone": "Asia/Taipei",
    "emergency_numbers": {
        "119": "消防局救護車",
        "110": "警察局",
        "112": "行動電話國際緊急號碼",
        "113": "保護專線",
        "165": "反詐騙諮詢專線"
    }
}
```

## 🛠️ Development Workflow

### 1. RED Phase (Write Failing Tests)
```bash
# Create test files first
python -m pytest tests/ -v  # Should fail initially
```

### 2. GREEN Phase (Minimal Implementation)
```bash
# Implement just enough to pass tests
python -m pytest tests/ -v  # Should pass
```

### 3. REFACTOR Phase (Improve Code)
```bash
# Refactor while keeping tests green
python -m pytest tests/ -v  # Should still pass
```

### 4. Validation Phase
```bash
# Run all validations
node validators/code-quality-validator.js
node validators/taiwan-compliance-validator.js
```

## 📋 Best Practices

### Medical AI Development
1. **Always prioritize safety** - emergency keywords trigger immediate 119 guidance
2. **Never provide diagnoses** - use advisory language only
3. **Include disclaimers** - every medical response needs disclaimer
4. **Protect privacy** - mask all PII before processing
5. **Test thoroughly** - medical safety cannot be compromised

### Taiwan Localization
1. **Use Traditional Chinese** - avoid simplified characters
2. **Configure locale properly** - zh-TW throughout
3. **Include emergency numbers** - all five critical numbers
4. **Follow PDPA** - implement data protection measures
5. **Localize APIs** - use Taiwan parameters for external services

### Test-Driven Development
1. **Write tests first** - understand requirements through tests
2. **Keep tests simple** - one assertion per test
3. **Test edge cases** - especially medical safety scenarios
4. **Maintain coverage** - 80% minimum for medical components
5. **Mock external services** - use respx for HTTP calls

## 🚨 Critical Safety Rules

### Medical Safety
- ❌ Never provide definitive medical diagnoses
- ✅ Always include medical disclaimers
- ✅ Detect emergency keywords immediately
- ✅ Provide 119 guidance for emergencies
- ✅ Mask all personal information

### Taiwan Compliance
- ✅ Use Traditional Chinese (zh-TW) only
- ✅ Include all Taiwan emergency numbers
- ✅ Implement PDPA data protection
- ✅ Configure proper timezone (Asia/Taipei)
- ✅ Use Taiwan parameters for APIs

## 📚 Documentation

- [FastAPI Medical Patterns](./workflows/fastapi-medical-patterns.py) - Complete medical service implementation
- [TDD Workflow](./workflows/tdd-medical-workflow.js) - Test-driven development process
- [Medical Safety Testing](./templates/medical-tdd-template.py) - Medical safety test templates
- [Taiwan Compliance](./validators/taiwan-compliance-validator.js) - Compliance validation

## 🔗 Integration with Claude Code

This implementation framework is designed to work with Claude Code CLI for automated task execution:

```bash
# Use with Claude Code Task tool
claude task execute --spec-file tasks.md --task-id 1.1 --executor spec-task-executor
```

The framework automatically handles:
- Coordination hooks for progress tracking
- Memory storage for implementation state
- Real-time notifications for task updates
- Integration with existing project structure

## 🎯 Goals Achieved

✅ **Clean, tested implementation** - TDD workflow ensures quality
✅ **Medical safety compliance** - Emergency handling and disclaimers
✅ **Taiwan localization** - Traditional Chinese and local requirements
✅ **PDPA compliance** - Privacy protection and data masking
✅ **FastAPI best practices** - Async patterns and proper structure
✅ **Automated validation** - Code quality and compliance checking
✅ **Progress tracking** - Comprehensive metrics and reporting
✅ **Reusable templates** - Accelerated development for medical AI

This implementation framework provides everything needed to build production-ready medical AI applications with Taiwan compliance and medical safety as core requirements.