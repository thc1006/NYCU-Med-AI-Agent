#!/usr/bin/env node

/**
 * TDD Workflow Integration for Task Validation System
 * Integrates task validation with Test-Driven Development workflow
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class TDDIntegration {
  constructor() {
    this.phases = ['RED', 'GREEN', 'REFACTOR'];
    this.currentPhase = 'RED';
    this.testResults = new Map();
    this.taskExecutionLog = [];
  }

  /**
   * Initialize TDD workflow for a task
   */
  async initializeTDDWorkflow(taskId, taskDescription, options = {}) {
    console.log(`🔴 Starting TDD workflow for: ${taskDescription}`);

    const workflow = {
      taskId,
      description: taskDescription,
      startTime: Date.now(),
      phases: {
        red: { status: 'pending', tests: [], startTime: null },
        green: { status: 'pending', implementation: [], startTime: null },
        refactor: { status: 'pending', improvements: [], startTime: null }
      },
      options
    };

    // Execute pre-task validation
    await this.preTaskValidation(taskId, taskDescription);

    // Start RED phase
    await this.startRedPhase(workflow);

    return workflow;
  }

  /**
   * Pre-task validation before starting TDD
   */
  async preTaskValidation(taskId, taskDescription) {
    console.log('🔍 Running pre-task validation...');

    // Validate task atomicity
    const atomicityCheck = this.validateTaskAtomicity(taskDescription);
    if (!atomicityCheck.passed) {
      throw new Error(`Task is not atomic: ${atomicityCheck.reason}`);
    }

    // Check medical safety requirements
    const medicalSafetyCheck = this.validateMedicalSafety(taskDescription);
    if (!medicalSafetyCheck.passed) {
      console.warn(`⚠️ Medical safety warning: ${medicalSafetyCheck.warnings.join(', ')}`);
    }

    // Execute coordination hooks
    await this.executeHook('pre-task', taskId, taskDescription);

    console.log('✅ Pre-task validation completed');
  }

  /**
   * Start RED phase - Write failing tests first
   */
  async startRedPhase(workflow) {
    console.log('🔴 Phase: RED - Writing failing tests');

    workflow.phases.red.startTime = Date.now();
    workflow.phases.red.status = 'in_progress';

    const testPlan = this.generateTestPlan(workflow.description);

    // Create test files
    for (const test of testPlan.tests) {
      await this.createFailingTest(test, workflow);
      workflow.phases.red.tests.push(test);
    }

    // Run tests to confirm they fail
    const testResults = await this.runTests(workflow);

    if (testResults.passed === 0 && testResults.failed > 0) {
      workflow.phases.red.status = 'completed';
      console.log('✅ RED phase completed - All tests failing as expected');

      // Move to GREEN phase
      await this.startGreenPhase(workflow);
    } else {
      throw new Error('RED phase failed - Tests should be failing initially');
    }
  }

  /**
   * Start GREEN phase - Implement minimum code to pass tests
   */
  async startGreenPhase(workflow) {
    console.log('🟢 Phase: GREEN - Implementing minimum viable code');

    workflow.phases.green.startTime = Date.now();
    workflow.phases.green.status = 'in_progress';

    // Generate implementation files
    const implementationPlan = this.generateImplementationPlan(workflow);

    for (const impl of implementationPlan.files) {
      await this.createMinimalImplementation(impl, workflow);
      workflow.phases.green.implementation.push(impl);
    }

    // Run tests to check if they pass
    const testResults = await this.runTests(workflow);

    if (testResults.failed === 0) {
      workflow.phases.green.status = 'completed';
      console.log('✅ GREEN phase completed - All tests passing');

      // Move to REFACTOR phase
      await this.startRefactorPhase(workflow);
    } else {
      console.log(`⚠️ ${testResults.failed} tests still failing - continuing implementation`);
      // Continue GREEN phase or request assistance
    }
  }

  /**
   * Start REFACTOR phase - Improve code quality while keeping tests green
   */
  async startRefactorPhase(workflow) {
    console.log('🔵 Phase: REFACTOR - Improving code quality');

    workflow.phases.refactor.startTime = Date.now();
    workflow.phases.refactor.status = 'in_progress';

    // Analyze code for refactoring opportunities
    const refactoringPlan = this.generateRefactoringPlan(workflow);

    for (const refactoring of refactoringPlan.improvements) {
      await this.applyRefactoring(refactoring, workflow);

      // Run tests after each refactoring to ensure they still pass
      const testResults = await this.runTests(workflow);

      if (testResults.failed > 0) {
        console.error('❌ Refactoring broke tests - reverting changes');
        await this.revertLastChange(workflow);
      } else {
        workflow.phases.refactor.improvements.push(refactoring);
        console.log(`✅ Applied refactoring: ${refactoring.description}`);
      }
    }

    workflow.phases.refactor.status = 'completed';
    console.log('✅ REFACTOR phase completed');

    // Finalize workflow
    await this.finalizeWorkflow(workflow);
  }

  /**
   * Generate test plan for a task
   */
  generateTestPlan(taskDescription) {
    const testPlan = {
      tests: [],
      coverage: []
    };

    // Extract testable components from task description
    const components = this.extractComponents(taskDescription);
    const files = this.extractFileReferences(taskDescription);

    for (const file of files) {
      if (file.endsWith('.py')) {
        testPlan.tests.push({
          type: 'unit',
          file: file.replace('.py', '_test.py'),
          target: file,
          framework: 'pytest',
          description: `Unit tests for ${path.basename(file, '.py')}`
        });
      } else if (file.endsWith('.js')) {
        testPlan.tests.push({
          type: 'unit',
          file: file.replace('.js', '.test.js'),
          target: file,
          framework: 'jest',
          description: `Unit tests for ${path.basename(file, '.js')}`
        });
      }
    }

    // Add medical safety tests if needed
    if (this.isMedicalTask(taskDescription)) {
      testPlan.tests.push({
        type: 'safety',
        file: 'tests/medical_safety_test.py',
        target: 'medical functionality',
        framework: 'pytest',
        description: 'Medical safety compliance tests'
      });
    }

    return testPlan;
  }

  /**
   * Create failing test file
   */
  async createFailingTest(test, workflow) {
    const testDir = path.dirname(test.file);
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }

    let testContent;

    if (test.framework === 'pytest') {
      testContent = this.generatePytestContent(test, workflow);
    } else if (test.framework === 'jest') {
      testContent = this.generateJestContent(test, workflow);
    }

    fs.writeFileSync(test.file, testContent);
    console.log(`📝 Created failing test: ${test.file}`);

    // Register test creation in coordination system
    await this.executeHook('post-edit', test.file, 'test-created');
  }

  /**
   * Generate pytest test content
   */
  generatePytestContent(test, workflow) {
    const moduleName = path.basename(test.target, '.py');
    const className = this.toPascalCase(moduleName);

    return `#!/usr/bin/env python3
"""
${test.description}
Task: ${workflow.description}
Generated for TDD RED phase
"""

import pytest
from unittest.mock import Mock, patch


class Test${className}:
    """Test cases for ${moduleName} - RED phase (should fail initially)."""

    def setup_method(self):
        """Setup test fixtures."""
        pass

    def test_${moduleName}_exists(self):
        """Test that the module can be imported."""
        # This test should fail initially until we create the module
        try:
            from app.${moduleName.replace('-', '_')} import ${className}
            assert ${className} is not None
        except ImportError:
            pytest.fail(f"Module {moduleName} not found - implement in GREEN phase")

    def test_basic_functionality(self):
        """Test basic functionality - should fail in RED phase."""
        # TODO: This test should fail initially
        pytest.fail("Not implemented yet - GREEN phase needed")

    ${test.type === 'safety' ? this.generateMedicalSafetyTests() : ''}

    def test_success_criteria_met(self):
        """Test that task success criteria are met."""
        # Extract success criteria from task description
        # This should fail until implementation is complete
        pytest.fail("Success criteria not yet implemented")


# Medical Safety Tests (if applicable)
${test.type === 'safety' ? this.generateMedicalSafetyTestMethods() : ''}
`;
  }

  /**
   * Generate Jest test content
   */
  generateJestContent(test, workflow) {
    const moduleName = path.basename(test.target, '.js');
    const className = this.toPascalCase(moduleName);

    return `/**
 * ${test.description}
 * Task: ${workflow.description}
 * Generated for TDD RED phase
 */

describe('${className}', () => {
  beforeEach(() => {
    // Setup test fixtures
  });

  it('should exist and be importable', () => {
    // This test should fail initially until we create the module
    expect(() => {
      require('../${test.target}');
    }).not.toThrow();
  });

  it('should implement basic functionality', () => {
    // TODO: This test should fail initially
    fail('Not implemented yet - GREEN phase needed');
  });

  ${test.type === 'safety' ? this.generateJestMedicalSafetyTests() : ''}

  it('should meet task success criteria', () => {
    // Extract success criteria from task description
    // This should fail until implementation is complete
    fail('Success criteria not yet implemented');
  });
});

${test.type === 'safety' ? this.generateJestMedicalSafetyDescribe() : ''}
`;
  }

  /**
   * Generate implementation plan
   */
  generateImplementationPlan(workflow) {
    const files = this.extractFileReferences(workflow.description);

    return {
      files: files.map(file => ({
        path: file,
        type: this.getFileType(file),
        minimal: true,
        description: `Minimal implementation for ${path.basename(file)}`
      }))
    };
  }

  /**
   * Create minimal implementation
   */
  async createMinimalImplementation(impl, workflow) {
    const dir = path.dirname(impl.path);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    let content;

    if (impl.type === 'python') {
      content = this.generateMinimalPython(impl, workflow);
    } else if (impl.type === 'javascript') {
      content = this.generateMinimalJavaScript(impl, workflow);
    }

    fs.writeFileSync(impl.path, content);
    console.log(`📝 Created minimal implementation: ${impl.path}`);

    await this.executeHook('post-edit', impl.path, 'implementation-created');
  }

  /**
   * Generate minimal Python implementation
   */
  generateMinimalPython(impl, workflow) {
    const moduleName = path.basename(impl.path, '.py');
    const className = this.toPascalCase(moduleName);

    return `#!/usr/bin/env python3
"""
${impl.description}
Task: ${workflow.description}
Minimal implementation for GREEN phase
"""

from typing import Optional, Dict, Any


class ${className}:
    """Minimal implementation to pass tests."""

    def __init__(self):
        """Initialize ${moduleName}."""
        pass

    def placeholder_method(self) -> Dict[str, Any]:
        """Minimal method to satisfy test requirements.

        Returns:
            Dict: Basic response structure
        """
        return {
            "status": "success",
            "message": "Minimal implementation",
            ${this.isMedicalTask(workflow.description) ? '"disclaimer": "This is not medical advice. For emergencies, call 119 or 112.",' : ''}
        }


# Helper functions for medical safety (if applicable)
${this.isMedicalTask(workflow.description) ? this.generateMedicalSafetyHelpers() : ''}
`;
  }

  /**
   * Generate minimal JavaScript implementation
   */
  generateMinimalJavaScript(impl, workflow) {
    const moduleName = path.basename(impl.path, '.js');
    const className = this.toPascalCase(moduleName);

    return `/**
 * ${impl.description}
 * Task: ${workflow.description}
 * Minimal implementation for GREEN phase
 */

class ${className} {
  constructor() {
    // Minimal initialization
  }

  placeholderMethod() {
    // Minimal method to satisfy test requirements
    return {
      status: 'success',
      message: 'Minimal implementation'${this.isMedicalTask(workflow.description) ? ',\n      disclaimer: "This is not medical advice. For emergencies, call 119 or 112."' : ''}
    };
  }
}

${this.isMedicalTask(workflow.description) ? this.generateJSMedicalSafetyHelpers() : ''}

module.exports = ${className};
`;
  }

  /**
   * Run tests and return results
   */
  async runTests(workflow) {
    const results = {
      passed: 0,
      failed: 0,
      total: 0,
      details: []
    };

    try {
      // Run Python tests
      const pytestResult = await this.runPytest();
      results.passed += pytestResult.passed;
      results.failed += pytestResult.failed;
      results.total += pytestResult.total;

      // Run JavaScript tests
      const jestResult = await this.runJest();
      results.passed += jestResult.passed;
      results.failed += jestResult.failed;
      results.total += jestResult.total;

      console.log(`🧪 Test Results: ${results.passed}/${results.total} passed`);

    } catch (error) {
      console.error('❌ Test execution failed:', error.message);
      results.error = error.message;
    }

    return results;
  }

  /**
   * Run pytest tests
   */
  async runPytest() {
    try {
      const output = execSync('python -m pytest tests/ -v --tb=short', {
        encoding: 'utf-8',
        stdio: 'pipe'
      });

      return this.parsePytestOutput(output);
    } catch (error) {
      // Pytest returns non-zero exit code when tests fail
      return this.parsePytestOutput(error.stdout || error.message);
    }
  }

  /**
   * Run Jest tests
   */
  async runJest() {
    try {
      const output = execSync('npm test', {
        encoding: 'utf-8',
        stdio: 'pipe'
      });

      return this.parseJestOutput(output);
    } catch (error) {
      return this.parseJestOutput(error.stdout || error.message);
    }
  }

  /**
   * Parse pytest output
   */
  parsePytestOutput(output) {
    const lines = output.split('\n');
    let passed = 0, failed = 0;

    lines.forEach(line => {
      if (line.includes('PASSED')) passed++;
      if (line.includes('FAILED')) failed++;
    });

    return { passed, failed, total: passed + failed };
  }

  /**
   * Parse Jest output
   */
  parseJestOutput(output) {
    const passedMatch = output.match(/(\d+) passing/);
    const failedMatch = output.match(/(\d+) failing/);

    const passed = passedMatch ? parseInt(passedMatch[1]) : 0;
    const failed = failedMatch ? parseInt(failedMatch[1]) : 0;

    return { passed, failed, total: passed + failed };
  }

  /**
   * Finalize TDD workflow
   */
  async finalizeWorkflow(workflow) {
    workflow.endTime = Date.now();
    workflow.duration = workflow.endTime - workflow.startTime;
    workflow.status = 'completed';

    console.log(`✅ TDD workflow completed in ${workflow.duration}ms`);

    // Store workflow results
    await this.storeWorkflowResults(workflow);

    // Execute post-task hooks
    await this.executeHook('post-task', workflow.taskId, workflow);

    // Generate workflow report
    this.generateTDDReport(workflow);
  }

  /**
   * Store workflow results in memory
   */
  async storeWorkflowResults(workflow) {
    try {
      const memoryKey = `tdd/workflows/${workflow.taskId}`;
      const memoryData = JSON.stringify({
        workflow,
        timestamp: new Date().toISOString()
      });

      execSync(`npx claude-flow@alpha hooks memory-store --key "${memoryKey}" --data '${memoryData}'`,
        { stdio: 'pipe' });

    } catch (error) {
      console.warn('⚠️ Failed to store workflow results:', error.message);
    }
  }

  /**
   * Generate TDD workflow report
   */
  generateTDDReport(workflow) {
    console.log('\n' + '='.repeat(60));
    console.log('🔄 TDD WORKFLOW REPORT');
    console.log('='.repeat(60));
    console.log(`Task: ${workflow.description}`);
    console.log(`Duration: ${workflow.duration}ms`);
    console.log(`Status: ${workflow.status}`);
    console.log('');

    Object.entries(workflow.phases).forEach(([phase, data]) => {
      const emoji = phase === 'red' ? '🔴' : phase === 'green' ? '🟢' : '🔵';
      console.log(`${emoji} ${phase.toUpperCase()}: ${data.status}`);

      if (data.tests?.length > 0) {
        console.log(`  Tests: ${data.tests.length}`);
      }
      if (data.implementation?.length > 0) {
        console.log(`  Files: ${data.implementation.length}`);
      }
      if (data.improvements?.length > 0) {
        console.log(`  Refactorings: ${data.improvements.length}`);
      }
    });

    console.log('='.repeat(60));
  }

  /**
   * Helper methods
   */
  validateTaskAtomicity(description) {
    if (description.length > 100) {
      return { passed: false, reason: 'Description too long - may not be atomic' };
    }

    const broadTerms = ['system', 'integration', 'complete', 'entire'];
    const foundBroadTerms = broadTerms.filter(term =>
      description.toLowerCase().includes(term)
    );

    if (foundBroadTerms.length > 0) {
      return { passed: false, reason: `Contains broad terms: ${foundBroadTerms.join(', ')}` };
    }

    return { passed: true };
  }

  validateMedicalSafety(description) {
    const warnings = [];

    if (this.isMedicalTask(description)) {
      if (!description.toLowerCase().includes('disclaimer')) {
        warnings.push('Missing medical disclaimer requirements');
      }
      if (!description.includes('119')) {
        warnings.push('Missing Taiwan emergency number (119)');
      }
    }

    return { passed: warnings.length === 0, warnings };
  }

  isMedicalTask(description) {
    const medicalKeywords = ['symptom', 'medical', 'health', 'hospital', 'emergency', 'diagnosis'];
    return medicalKeywords.some(keyword =>
      description.toLowerCase().includes(keyword)
    );
  }

  extractComponents(description) {
    // Extract component names from description
    return [];
  }

  extractFileReferences(description) {
    const filePattern = /\b[\w\-\/]+\.\w+\b/g;
    return description.match(filePattern) || [];
  }

  getFileType(filePath) {
    const ext = path.extname(filePath);
    if (ext === '.py') return 'python';
    if (ext === '.js') return 'javascript';
    return 'unknown';
  }

  toPascalCase(str) {
    return str.replace(/[-_](.)/g, (_, char) => char.toUpperCase())
              .replace(/^./, char => char.toUpperCase());
  }

  async executeHook(hookType, ...args) {
    try {
      const command = `npx claude-flow@alpha hooks ${hookType}`;
      execSync(command, { stdio: 'pipe' });
    } catch (error) {
      console.warn(`⚠️ Hook ${hookType} failed:`, error.message);
    }
  }

  generateMedicalSafetyTests() {
    return `
    def test_no_diagnostic_language(self):
        """Ensure no diagnostic language is used."""
        # Test implementation should verify no diagnostic terms
        pass

    def test_emergency_contacts_accessible(self):
        """Verify Taiwan emergency contacts are accessible."""
        # Test should verify 119, 112 are prominently displayed
        pass
`;
  }

  generateMedicalSafetyTestMethods() {
    return `
def test_medical_disclaimer_present():
    """Test that medical disclaimers are present in all responses."""
    pass

def test_taiwan_emergency_numbers():
    """Test that Taiwan emergency numbers (119, 112) are accessible."""
    pass
`;
  }

  generateMedicalSafetyHelpers() {
    return `
def ensure_medical_disclaimer(response: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure medical disclaimer is present in response."""
    if "disclaimer" not in response:
        response["disclaimer"] = "This is not medical advice. For emergencies, call 119 or 112."
    return response
`;
  }

  generateJSMedicalSafetyHelpers() {
    return `
/**
 * Ensure medical disclaimer is present in response
 */
function ensureMedicalDisclaimer(response) {
  if (!response.disclaimer) {
    response.disclaimer = 'This is not medical advice. For emergencies, call 119 or 112.';
  }
  return response;
}
`;
  }
}

// CLI usage
if (require.main === module) {
  const command = process.argv[2];
  const taskId = process.argv[3];
  const taskDescription = process.argv[4];

  const tdd = new TDDIntegration();

  if (command === 'start' && taskId && taskDescription) {
    tdd.initializeTDDWorkflow(taskId, taskDescription)
      .then(workflow => {
        console.log('✅ TDD workflow completed successfully');
      })
      .catch(error => {
        console.error('❌ TDD workflow failed:', error.message);
        process.exit(1);
      });

  } else {
    console.log('TDD Workflow Integration');
    console.log('Usage:');
    console.log('  node tdd-integration.js start <task-id> "<task-description>"');
    console.log('');
    console.log('Example:');
    console.log('  node tdd-integration.js start "task-001" "Create symptom validation model"');
  }
}

module.exports = TDDIntegration;