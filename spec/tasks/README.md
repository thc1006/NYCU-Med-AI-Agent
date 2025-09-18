# Task Management System

This directory contains the comprehensive task breakdown and validation system for the Medical AI Agent project.

## Directory Structure

- `templates/` - Task decomposition templates for medical features
- `validators/` - Task validation tools and rules
- `executors/` - Task execution framework
- `medical/` - Taiwan-specific medical task considerations

## Core Components

1. **Task Validator** (`validators/spec-task-validator.js`) - Validates task atomicity and implementability
2. **Task Templates** (`templates/`) - Standardized task breakdowns for medical features
3. **Task Executor** (`executors/spec-task-executor.js`) - Clean task implementation framework
4. **Traceability System** - Maps tasks to specifications and requirements

## Usage

### Validate Tasks
```bash
node spec/tasks/validators/spec-task-validator.js path/to/tasks.md
```

### Execute Task
```bash
node spec/tasks/executors/spec-task-executor.js task-id
```

### Generate Template
```bash
node spec/tasks/templates/generate-template.js feature-name
```

## Key Principles

- **Atomic**: Each task should be completable in 15-30 minutes
- **Testable**: Clear success criteria and verification steps
- **Safe**: Medical safety validation at task level
- **Traceable**: Maps to specific requirements and specifications
- **Taiwan-focused**: Considers local medical regulations and practices