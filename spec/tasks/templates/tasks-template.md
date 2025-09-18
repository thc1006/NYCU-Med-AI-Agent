# Tasks Template

This template provides the standard structure for atomic task breakdown documents in the Medical AI Agent project.

## Task Overview

Brief description of the feature or component being broken down into tasks.

## Steering Document Compliance

Reference to requirements and design documents that these tasks implement:
- Requirements: [path/to/requirements.md]
- Design: [path/to/design.md]

## Atomic Task Requirements

All tasks in this document must meet these criteria:

### 1. **Atomicity**
- ✅ Completable in 15-30 minutes by experienced developer
- ✅ Touches 1-3 related files maximum
- ✅ Single, testable outcome
- ✅ Specific file paths identified

### 2. **Agent-Friendly Format**
- ✅ Clear action verbs (create, implement, write, test, build)
- ✅ Measurable success criteria
- ✅ Minimal context switching required
- ✅ Explicit input/output specifications

### 3. **Medical Safety**
- ✅ No diagnostic language in implementation tasks
- ✅ Disclaimer requirements clearly specified
- ✅ Emergency contact integration requirements
- ✅ Taiwan medical regulation compliance

### 4. **Requirements Traceability**
- ✅ Each task references specific requirements (REQ-XX)
- ✅ Leverages existing code where applicable
- ✅ Clear dependencies between tasks

## Task Format Guidelines

### Checkbox Format
```
- [ ] 1. Task description with REQ-XX reference
  - **Files**: specific/file/paths.js
  - **Success**: Clear verification criteria
  - **Leverage**: existing code or patterns to build upon
```

### Medical Task Considerations
- Always include disclaimer requirements
- Specify Taiwan emergency numbers (119, 112)
- Reference MOHW/health regulations where applicable
- Ensure zh-TW language support

### Dependencies
- List prerequisite tasks clearly
- Minimize sequential dependencies
- Allow parallel execution where possible

## Tasks

### Core Implementation

- [ ] 1. Setup basic project structure with health check endpoint (REQ-01)
  - **Files**: app/main.py, tests/test_health.py
  - **Success**: GET /healthz returns 200 with {"status":"ok"}
  - **Leverage**: FastAPI project template

- [ ] 2. Implement configuration management with Taiwan defaults (REQ-02)
  - **Files**: app/config.py, .env.example
  - **Success**: Environment variables loaded with zh-TW defaults
  - **Leverage**: Pydantic BaseSettings pattern

### Feature Implementation

- [ ] 3. Create symptom input validation with safety checks (REQ-03)
  - **Files**: app/domain/models.py, tests/test_models.py
  - **Success**: Pydantic models validate input and reject diagnostic language
  - **Leverage**: FastAPI request validation

- [ ] 4. Implement emergency keyword detection system (REQ-04)
  - **Files**: app/domain/triage.py, tests/test_triage.py
  - **Success**: Keywords like "chest pain" trigger emergency response
  - **Leverage**: Rule-based pattern matching

### Integration Tasks

- [ ] 5. Connect Google Places API with Taiwan localization (REQ-05)
  - **Files**: app/services/places.py, tests/test_places.py
  - **Success**: API calls use zh-TW and return Taiwan hospitals
  - **Leverage**: httpx client with proper headers

- [ ] 6. Add medical disclaimers to all responses (REQ-06)
  - **Files**: app/middlewares/medical_disclaimer.py
  - **Success**: All medical responses include disclaimers and 119 reference
  - **Leverage**: FastAPI middleware pattern

### Testing and Validation

- [ ] 7. Create comprehensive test suite with medical safety validation (REQ-07)
  - **Files**: tests/integration/test_safety.py
  - **Success**: Tests verify no diagnostic language in responses
  - **Leverage**: pytest fixtures and parametrized tests

- [ ] 8. Implement end-to-end workflow testing (REQ-08)
  - **Files**: tests/e2e/test_workflow.py
  - **Success**: Complete user journey from symptom to hospital recommendation
  - **Leverage**: TestClient for API testing

## Validation Checklist

Before marking this task document complete, verify:

- [ ] All tasks reference specific requirements
- [ ] File paths are explicit and achievable
- [ ] Medical safety considerations included
- [ ] Taiwan localization requirements specified
- [ ] Dependencies between tasks are minimal
- [ ] Success criteria are measurable
- [ ] No task exceeds 30-minute completion time
- [ ] Emergency protocols (119, 112) properly integrated

## Notes

- Tasks must be implemented in order unless explicitly marked as parallel
- Each completed task should trigger validation hooks
- Medical content requires additional safety review
- Taiwan regulatory compliance must be maintained throughout