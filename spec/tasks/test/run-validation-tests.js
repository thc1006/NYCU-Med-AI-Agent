#!/usr/bin/env node

/**
 * End-to-End Test Suite for Task Validation System
 * Tests all components of the task validation and execution system
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class ValidationSystemTester {
  constructor() {
    this.testResults = {
      passed: 0,
      failed: 0,
      total: 0,
      details: []
    };

    this.testData = {
      validTask: this.createValidTaskDocument(),
      invalidTask: this.createInvalidTaskDocument(),
      medicalTask: this.createMedicalTaskDocument()
    };
  }

  /**
   * Run all validation system tests
   */
  async runAllTests() {
    console.log('🧪 Starting Task Validation System Tests');
    console.log('='.repeat(60));

    try {
      // Setup test environment
      await this.setupTestEnvironment();

      // Test individual validators
      await this.testTaskValidator();
      await this.testMedicalValidator();
      await this.testTraceabilitySystem();

      // Test automation pipeline
      await this.testValidationPipeline();

      // Test TDD integration
      await this.testTDDIntegration();

      // Test task executor
      await this.testTaskExecutor();

      // Test template generation
      await this.testTemplateGeneration();

      // Cleanup
      await this.cleanupTestEnvironment();

      // Generate final report
      this.generateTestReport();

    } catch (error) {
      console.error('❌ Test suite failed:', error.message);
      process.exit(1);
    }
  }

  /**
   * Setup test environment
   */
  async setupTestEnvironment() {
    console.log('🔧 Setting up test environment...');

    // Create test directories
    const testDirs = [
      'spec/test-data',
      'spec/test-data/valid',
      'spec/test-data/invalid',
      'spec/test-data/medical'
    ];

    testDirs.forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });

    // Create test task documents
    fs.writeFileSync('spec/test-data/valid/tasks.md', this.testData.validTask);
    fs.writeFileSync('spec/test-data/invalid/tasks.md', this.testData.invalidTask);
    fs.writeFileSync('spec/test-data/medical/tasks.md', this.testData.medicalTask);

    // Create mock requirements and design documents
    fs.writeFileSync('spec/test-data/valid/requirements.md', this.createMockRequirements());
    fs.writeFileSync('spec/test-data/valid/design.md', this.createMockDesign());

    console.log('✅ Test environment setup complete');
  }

  /**
   * Test the main task validator
   */
  async testTaskValidator() {
    console.log('🔍 Testing Task Validator...');

    try {
      // Test valid task document
      const validResult = await this.runValidator(
        'validators/spec-task-validator.js',
        'spec/test-data/valid/tasks.md'
      );

      this.assertEqual(validResult.rating, 'PASS', 'Valid task should pass validation');

      // Test invalid task document
      const invalidResult = await this.runValidator(
        'validators/spec-task-validator.js',
        'spec/test-data/invalid/tasks.md'
      );

      this.assertNotEqual(invalidResult.rating, 'PASS', 'Invalid task should fail validation');

      console.log('✅ Task Validator tests passed');

    } catch (error) {
      this.recordFailure('Task Validator', error.message);
    }
  }

  /**
   * Test Taiwan medical validator
   */
  async testMedicalValidator() {
    console.log('🏥 Testing Taiwan Medical Validator...');

    try {
      const TaiwanMedicalValidator = require('../medical/taiwan-medical-validation.js');
      const validator = new TaiwanMedicalValidator();

      // Test medical task validation
      const result = validator.validateMedicalTask(this.testData.medicalTask);

      this.assertTrue(result.taiwanSpecific.emergencyNumbers, 'Should detect emergency numbers');
      this.assertTrue(result.taiwanSpecific.languageSupport, 'Should detect language support');

      // Test diagnostic language detection
      const diagnosticText = 'This system will diagnose your symptoms and cure your illness';
      const diagnosticResult = validator.validateMedicalTask(diagnosticText);

      this.assertFalse(diagnosticResult.compliant, 'Should fail on diagnostic language');

      console.log('✅ Taiwan Medical Validator tests passed');

    } catch (error) {
      this.recordFailure('Taiwan Medical Validator', error.message);
    }
  }

  /**
   * Test traceability system
   */
  async testTraceabilitySystem() {
    console.log('🔗 Testing Traceability System...');

    try {
      const TraceabilitySystem = require('../automation/traceability-system.js');
      const traceability = new TraceabilitySystem();

      await traceability.initialize('spec/test-data/valid');

      const { validation } = traceability.generateTraceabilityReport();

      this.assertGreaterThan(validation.requirementsCoverage, 50, 'Should have reasonable requirements coverage');

      console.log('✅ Traceability System tests passed');

    } catch (error) {
      this.recordFailure('Traceability System', error.message);
    }
  }

  /**
   * Test validation pipeline
   */
  async testValidationPipeline() {
    console.log('⚙️ Testing Validation Pipeline...');

    try {
      const ValidationPipeline = require('../automation/validation-pipeline.js');
      const pipeline = new ValidationPipeline();

      const result = await pipeline.runValidation('spec/test-data/valid/tasks.md', {
        reportFormat: 'summary'
      });

      this.assertNotNull(result.overall, 'Pipeline should return overall result');
      this.assertGreaterThan(result.score, 0, 'Pipeline should calculate score');

      console.log('✅ Validation Pipeline tests passed');

    } catch (error) {
      this.recordFailure('Validation Pipeline', error.message);
    }
  }

  /**
   * Test TDD integration
   */
  async testTDDIntegration() {
    console.log('🔄 Testing TDD Integration...');

    try {
      const TDDIntegration = require('../automation/tdd-integration.js');
      const tdd = new TDDIntegration();

      // Test atomicity validation
      const atomicCheck = tdd.validateTaskAtomicity('Create simple validation function');
      this.assertTrue(atomicCheck.passed, 'Simple task should pass atomicity check');

      const nonAtomicCheck = tdd.validateTaskAtomicity('Build complete integrated system with all components and comprehensive testing framework');
      this.assertFalse(nonAtomicCheck.passed, 'Complex task should fail atomicity check');

      console.log('✅ TDD Integration tests passed');

    } catch (error) {
      this.recordFailure('TDD Integration', error.message);
    }
  }

  /**
   * Test task executor
   */
  async testTaskExecutor() {
    console.log('⚡ Testing Task Executor...');

    try {
      const TaskExecutor = require('../executors/spec-task-executor.js');
      const executor = new TaskExecutor();

      // Test file type detection
      this.assertEqual(executor.getFileType('test.py'), 'python', 'Should detect Python files');
      this.assertEqual(executor.getFileType('test.js'), 'javascript', 'Should detect JavaScript files');

      // Test medical content detection
      this.assertTrue(executor.isMedicalContent('symptom analysis'), 'Should detect medical content');
      this.assertFalse(executor.isMedicalContent('database connection'), 'Should not detect non-medical content');

      console.log('✅ Task Executor tests passed');

    } catch (error) {
      this.recordFailure('Task Executor', error.message);
    }
  }

  /**
   * Test template generation
   */
  async testTemplateGeneration() {
    console.log('📋 Testing Template Generation...');

    try {
      const TemplateGenerator = require('../templates/generate-template.js');
      const generator = new TemplateGenerator();

      const template = generator.generateTemplate('symptom-triage');

      this.assertContains(template, 'symptom', 'Should contain symptom-related content');
      this.assertContains(template, '119', 'Should contain Taiwan emergency numbers');
      this.assertContains(template, 'disclaimer', 'Should contain medical disclaimers');

      console.log('✅ Template Generation tests passed');

    } catch (error) {
      this.recordFailure('Template Generation', error.message);
    }
  }

  /**
   * Cleanup test environment
   */
  async cleanupTestEnvironment() {
    console.log('🧹 Cleaning up test environment...');

    try {
      // Remove test data directory
      if (fs.existsSync('spec/test-data')) {
        this.removeDirectory('spec/test-data');
      }

      console.log('✅ Cleanup complete');
    } catch (error) {
      console.warn('⚠️ Cleanup failed:', error.message);
    }
  }

  /**
   * Run a validator and return results
   */
  async runValidator(validatorPath, taskFile) {
    try {
      const ValidatorClass = require(`../${validatorPath}`);
      const validator = new ValidatorClass();
      return await validator.validateTaskDocument(taskFile);
    } catch (error) {
      throw new Error(`Validator execution failed: ${error.message}`);
    }
  }

  /**
   * Test assertion methods
   */
  assertEqual(actual, expected, message) {
    this.testResults.total++;
    if (actual === expected) {
      this.testResults.passed++;
      console.log(`  ✅ ${message}`);
    } else {
      this.testResults.failed++;
      console.log(`  ❌ ${message}: expected '${expected}', got '${actual}'`);
      this.testResults.details.push({
        type: 'assertEqual',
        message,
        expected,
        actual,
        passed: false
      });
    }
  }

  assertNotEqual(actual, expected, message) {
    this.testResults.total++;
    if (actual !== expected) {
      this.testResults.passed++;
      console.log(`  ✅ ${message}`);
    } else {
      this.testResults.failed++;
      console.log(`  ❌ ${message}: value should not equal '${expected}'`);
      this.testResults.details.push({
        type: 'assertNotEqual',
        message,
        expected: `not ${expected}`,
        actual,
        passed: false
      });
    }
  }

  assertTrue(actual, message) {
    this.assertEqual(actual, true, message);
  }

  assertFalse(actual, message) {
    this.assertEqual(actual, false, message);
  }

  assertNotNull(actual, message) {
    this.testResults.total++;
    if (actual != null) {
      this.testResults.passed++;
      console.log(`  ✅ ${message}`);
    } else {
      this.testResults.failed++;
      console.log(`  ❌ ${message}: value should not be null/undefined`);
      this.testResults.details.push({
        type: 'assertNotNull',
        message,
        actual,
        passed: false
      });
    }
  }

  assertGreaterThan(actual, expected, message) {
    this.testResults.total++;
    if (actual > expected) {
      this.testResults.passed++;
      console.log(`  ✅ ${message}`);
    } else {
      this.testResults.failed++;
      console.log(`  ❌ ${message}: ${actual} should be greater than ${expected}`);
      this.testResults.details.push({
        type: 'assertGreaterThan',
        message,
        expected: `> ${expected}`,
        actual,
        passed: false
      });
    }
  }

  assertContains(text, substring, message) {
    this.testResults.total++;
    if (text.includes(substring)) {
      this.testResults.passed++;
      console.log(`  ✅ ${message}`);
    } else {
      this.testResults.failed++;
      console.log(`  ❌ ${message}: text should contain '${substring}'`);
      this.testResults.details.push({
        type: 'assertContains',
        message,
        expected: `contains '${substring}'`,
        actual: 'not found',
        passed: false
      });
    }
  }

  recordFailure(component, error) {
    this.testResults.total++;
    this.testResults.failed++;
    console.log(`  ❌ ${component} failed: ${error}`);
    this.testResults.details.push({
      type: 'component_failure',
      component,
      error,
      passed: false
    });
  }

  /**
   * Generate final test report
   */
  generateTestReport() {
    console.log('\n' + '='.repeat(60));
    console.log('🧪 TASK VALIDATION SYSTEM TEST REPORT');
    console.log('='.repeat(60));
    console.log(`Total Tests: ${this.testResults.total}`);
    console.log(`Passed: ${this.testResults.passed}`);
    console.log(`Failed: ${this.testResults.failed}`);
    console.log(`Success Rate: ${((this.testResults.passed / this.testResults.total) * 100).toFixed(1)}%`);

    if (this.testResults.failed > 0) {
      console.log('\n❌ FAILED TESTS:');
      this.testResults.details
        .filter(detail => !detail.passed)
        .forEach((detail, i) => {
          console.log(`  ${i + 1}. ${detail.message || detail.component}`);
          if (detail.error) console.log(`     Error: ${detail.error}`);
        });
    }

    console.log('\n' + '='.repeat(60));

    if (this.testResults.failed === 0) {
      console.log('✅ All tests passed! Task validation system is working correctly.');
      process.exit(0);
    } else {
      console.log('❌ Some tests failed. Please review and fix issues.');
      process.exit(1);
    }
  }

  /**
   * Helper method to remove directory recursively
   */
  removeDirectory(dir) {
    if (fs.existsSync(dir)) {
      fs.readdirSync(dir).forEach(file => {
        const curPath = path.join(dir, file);
        if (fs.lstatSync(curPath).isDirectory()) {
          this.removeDirectory(curPath);
        } else {
          fs.unlinkSync(curPath);
        }
      });
      fs.rmdirSync(dir);
    }
  }

  /**
   * Test data creation methods
   */
  createValidTaskDocument() {
    return `# Valid Task Document

## Task Overview
Simple validation test with proper atomic tasks.

## Steering Document Compliance
- Requirements: REQ-01, REQ-02
- Design: design.md

## Atomic Task Requirements
All tasks meet atomicity criteria.

## Tasks

- [ ] 1. Create validation function with error handling (REQ-01)
  - **Files**: app/validation.py, tests/test_validation.py
  - **Success**: Function validates input and returns structured response
  - **Leverage**: Python validation patterns

- [ ] 2. Add medical disclaimer to responses (REQ-02)
  - **Files**: app/disclaimer.py
  - **Success**: All responses include Taiwan emergency contacts (119, 112)
  - **Leverage**: Medical safety templates
`;
  }

  createInvalidTaskDocument() {
    return `# Invalid Task Document

This document is missing required sections and has non-atomic tasks.

## Tasks

1. Build the entire integrated medical system with all components
2. Create comprehensive testing framework
3. Deploy to production with monitoring
`;
  }

  createMedicalTaskDocument() {
    return `# Medical Task Document

## Task Overview
Medical symptom analysis with Taiwan safety compliance.

## Tasks

- [ ] 1. Create symptom validation with emergency detection (REQ-MED-01)
  - **Files**: app/symptom_validator.py
  - **Success**: Detects emergency keywords and triggers 119 protocol
  - **Leverage**: Taiwan medical safety patterns
  - **Medical Safety**: Include disclaimers and emergency contacts (119, 112)

## Language Support
Traditional Chinese (zh-TW) for Taiwan localization.

## Emergency Protocols
- 119: Emergency Medical Services
- 112: International Emergency

## Medical Disclaimer
This system does not provide medical advice. For emergencies, call 119 or 112.
`;
  }

  createMockRequirements() {
    return `# Mock Requirements

## REQ-01: Input Validation
System must validate all user inputs with proper error handling.

## REQ-02: Medical Safety
All medical responses must include disclaimers and emergency contacts.

## REQ-MED-01: Emergency Detection
System must detect emergency symptoms and direct users to call 119.
`;
  }

  createMockDesign() {
    return `# Mock Design

## Component: Validation Service
Handles input validation and sanitization.

## API: Emergency Detection
Analyzes symptoms for emergency indicators.

## Model: Response Schema
Structured response format with disclaimers.
`;
  }
}

// CLI usage
if (require.main === module) {
  const tester = new ValidationSystemTester();
  tester.runAllTests();
}

module.exports = ValidationSystemTester;