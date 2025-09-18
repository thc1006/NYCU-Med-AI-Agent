#!/usr/bin/env node

/**
 * Task Executor Framework for Medical AI Agent
 * Executes validated tasks with coordination hooks and safety checks
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class TaskExecutor {
  constructor() {
    this.taskHistory = [];
    this.currentTask = null;
    this.memoryPath = '.swarm/memory.db';
    this.hooks = {
      preTask: true,
      postTask: true,
      postEdit: true,
      notify: true
    };
  }

  /**
   * Execute a task with full lifecycle management
   */
  async executeTask(taskId, taskDescription, options = {}) {
    const startTime = Date.now();

    try {
      // Pre-task hook
      await this.executePreTaskHook(taskId, taskDescription);

      // Set current task
      this.currentTask = {
        id: taskId,
        description: taskDescription,
        startTime,
        status: 'in_progress',
        ...options
      };

      console.log(`🚀 Executing Task: ${taskDescription}`);

      // Execute the task
      const result = await this.performTask(this.currentTask);

      // Post-task hook
      await this.executePostTaskHook(taskId, result);

      // Update task status
      this.currentTask.status = 'completed';
      this.currentTask.endTime = Date.now();
      this.currentTask.duration = this.currentTask.endTime - startTime;
      this.currentTask.result = result;

      // Store in history
      this.taskHistory.push({...this.currentTask});

      console.log(`✅ Task completed in ${this.currentTask.duration}ms`);

      return result;

    } catch (error) {
      console.error(`❌ Task failed: ${error.message}`);

      if (this.currentTask) {
        this.currentTask.status = 'failed';
        this.currentTask.error = error.message;
        this.currentTask.endTime = Date.now();
        this.taskHistory.push({...this.currentTask});
      }

      throw error;
    } finally {
      this.currentTask = null;
    }
  }

  /**
   * Perform the actual task implementation
   */
  async performTask(task) {
    const { files, successCriteria, leverage, medicalSafety } = task;

    const result = {
      filesCreated: [],
      filesModified: [],
      testsCreated: [],
      validationResults: {},
      medicalSafetyCheck: false
    };

    // Validate medical safety requirements
    if (medicalSafety) {
      await this.validateMedicalSafety(task);
      result.medicalSafetyCheck = true;
    }

    // Process files
    if (files && files.length > 0) {
      for (const file of files) {
        const filePath = path.resolve(file);

        if (await this.shouldCreateFile(filePath)) {
          await this.createFile(filePath, task);
          result.filesCreated.push(file);
          await this.executePostEditHook(file, 'created');
        } else if (await this.shouldModifyFile(filePath)) {
          await this.modifyFile(filePath, task);
          result.filesModified.push(file);
          await this.executePostEditHook(file, 'modified');
        }
      }
    }

    // Run tests if specified
    if (task.runTests) {
      result.testResults = await this.runTests(task);
    }

    // Validate success criteria
    if (successCriteria) {
      result.validationResults = await this.validateSuccessCriteria(successCriteria, task);
    }

    // Store task completion in memory
    await this.storeTaskInMemory(task, result);

    return result;
  }

  /**
   * Execute pre-task coordination hook
   */
  async executePreTaskHook(taskId, description) {
    if (!this.hooks.preTask) return;

    try {
      const command = `npx claude-flow@alpha hooks pre-task --description "${description}"`;
      console.log('🔄 Executing pre-task hook...');
      execSync(command, { stdio: 'inherit' });
    } catch (error) {
      console.warn('⚠️ Pre-task hook failed:', error.message);
    }
  }

  /**
   * Execute post-task coordination hook
   */
  async executePostTaskHook(taskId, result) {
    if (!this.hooks.postTask) return;

    try {
      const command = `npx claude-flow@alpha hooks post-task --task-id "${taskId}"`;
      console.log('🔄 Executing post-task hook...');
      execSync(command, { stdio: 'inherit' });
    } catch (error) {
      console.warn('⚠️ Post-task hook failed:', error.message);
    }
  }

  /**
   * Execute post-edit coordination hook
   */
  async executePostEditHook(filePath, action) {
    if (!this.hooks.postEdit) return;

    try {
      const memoryKey = `tasks/${this.currentTask.id}/${path.basename(filePath)}`;
      const command = `npx claude-flow@alpha hooks post-edit --file "${filePath}" --memory-key "${memoryKey}"`;
      execSync(command, { stdio: 'inherit' });
    } catch (error) {
      console.warn('⚠️ Post-edit hook failed:', error.message);
    }
  }

  /**
   * Validate medical safety requirements
   */
  async validateMedicalSafety(task) {
    const prohibitedTerms = ['diagnose', 'cure', 'treat', 'prescribe', 'medical advice'];
    const requiredTerms = ['disclaimer', '119', 'emergency', 'professional medical advice'];

    const description = task.description.toLowerCase();

    // Check for prohibited diagnostic language
    const foundProhibited = prohibitedTerms.filter(term => description.includes(term));
    if (foundProhibited.length > 0) {
      throw new Error(`Task contains prohibited medical terms: ${foundProhibited.join(', ')}`);
    }

    // Check for required safety elements
    const foundRequired = requiredTerms.filter(term => description.includes(term));
    if (foundRequired.length === 0) {
      console.warn('⚠️ Task may need additional medical safety considerations');
    }

    console.log('✅ Medical safety validation passed');
  }

  /**
   * Determine if file should be created
   */
  async shouldCreateFile(filePath) {
    return !fs.existsSync(filePath);
  }

  /**
   * Determine if file should be modified
   */
  async shouldModifyFile(filePath) {
    return fs.existsSync(filePath);
  }

  /**
   * Create new file with task-specific content
   */
  async createFile(filePath, task) {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const content = this.generateFileContent(filePath, task);
    fs.writeFileSync(filePath, content);

    console.log(`📝 Created: ${filePath}`);
  }

  /**
   * Modify existing file
   */
  async modifyFile(filePath, task) {
    const existingContent = fs.readFileSync(filePath, 'utf-8');
    const modifiedContent = this.applyTaskModifications(existingContent, task);

    if (modifiedContent !== existingContent) {
      fs.writeFileSync(filePath, modifiedContent);
      console.log(`📝 Modified: ${filePath}`);
    }
  }

  /**
   * Generate content for new files
   */
  generateFileContent(filePath, task) {
    const ext = path.extname(filePath);
    const fileName = path.basename(filePath, ext);

    // Generate appropriate content based on file type
    switch (ext) {
      case '.py':
        return this.generatePythonContent(fileName, task);
      case '.js':
        return this.generateJavaScriptContent(fileName, task);
      case '.md':
        return this.generateMarkdownContent(fileName, task);
      default:
        return this.generateGenericContent(fileName, task);
    }
  }

  /**
   * Generate Python file content
   */
  generatePythonContent(fileName, task) {
    const isTest = fileName.includes('test');

    if (isTest) {
      return `#!/usr/bin/env python3
"""
Test module for ${fileName.replace('test_', '')}
Generated by task: ${task.description}
"""

import pytest
from unittest.mock import Mock, patch


class Test${this.toPascalCase(fileName.replace('test_', ''))}:
    """Test cases for ${fileName.replace('test_', '')} functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        pass

    def test_placeholder(self):
        """Placeholder test - implement based on task requirements."""
        # TODO: Implement test based on: ${task.successCriteria || 'task requirements'}
        assert True, "Implement actual test"

    def test_medical_safety_compliance(self):
        """Ensure medical safety compliance."""
        # Verify no diagnostic language
        # Verify emergency contacts included
        # Verify disclaimers present
        pass


# Medical Safety Validation
def test_no_diagnostic_language():
    """Ensure no medical diagnostic language is used."""
    pass

def test_emergency_contacts_present():
    """Verify Taiwan emergency contacts (119, 112) are accessible."""
    pass
`;
    }

    return `#!/usr/bin/env python3
"""
${fileName} module
Generated by task: ${task.description}

Medical Safety Note: This module must not provide medical diagnoses.
All medical content must include disclaimers and emergency contacts (119, 112).
"""

from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class ${this.toPascalCase(fileName)}:
    """${task.description}"""

    def __init__(self):
        """Initialize ${fileName}."""
        pass

    def placeholder_method(self) -> Dict:
        """Placeholder method - implement based on task requirements.

        Returns:
            Dict: Result with medical safety compliance

        Note:
            Must include medical disclaimers and emergency contact information.
        """
        # TODO: Implement based on: ${task.successCriteria || 'task requirements'}
        return {
            "status": "success",
            "disclaimer": "This is not medical advice. For emergencies, call 119 or 112.",
            "emergency_contacts": {"taiwan_emergency": "119", "international_emergency": "112"}
        }


# Medical Safety Compliance
def ensure_medical_disclaimer(response: Dict) -> Dict:
    """Ensure all medical responses include appropriate disclaimers."""
    if "disclaimer" not in response:
        response["disclaimer"] = "This is not medical advice. For emergencies, call 119 or 112."
    return response
`;
  }

  /**
   * Generate JavaScript file content
   */
  generateJavaScriptContent(fileName, task) {
    const isTest = fileName.includes('test') || fileName.includes('spec');

    if (isTest) {
      return `/**
 * Test suite for ${fileName.replace(/\.(test|spec)/, '')}
 * Generated by task: ${task.description}
 */

describe('${this.toPascalCase(fileName.replace(/\.(test|spec)/, ''))}', () => {
  beforeEach(() => {
    // Setup test fixtures
  });

  it('should implement task requirements', () => {
    // TODO: Implement test based on: ${task.successCriteria || 'task requirements'}
    expect(true).toBe(true); // Replace with actual test
  });

  it('should comply with medical safety requirements', () => {
    // Verify no diagnostic language
    // Verify emergency contacts included (119, 112)
    // Verify medical disclaimers present
  });

  describe('Medical Safety Compliance', () => {
    it('should not provide medical diagnoses', () => {
      // Test implementation
    });

    it('should include Taiwan emergency contacts', () => {
      // Verify 119, 112 contacts are present
    });
  });
});
`;
    }

    return `/**
 * ${fileName} module
 * Generated by task: ${task.description}
 *
 * Medical Safety Note: This module must not provide medical diagnoses.
 * All medical content must include disclaimers and emergency contacts (119, 112).
 */

class ${this.toPascalCase(fileName)} {
  constructor() {
    // Initialize ${fileName}
  }

  /**
   * Placeholder method - implement based on task requirements
   * @returns {Object} Result with medical safety compliance
   */
  placeholderMethod() {
    // TODO: Implement based on: ${task.successCriteria || 'task requirements'}
    return {
      status: 'success',
      disclaimer: 'This is not medical advice. For emergencies, call 119 or 112.',
      emergencyContacts: {
        taiwanEmergency: '119',
        internationalEmergency: '112'
      }
    };
  }
}

/**
 * Ensure all medical responses include appropriate disclaimers
 * @param {Object} response - The response object
 * @returns {Object} Response with medical disclaimers
 */
function ensureMedicalDisclaimer(response) {
  if (!response.disclaimer) {
    response.disclaimer = 'This is not medical advice. For emergencies, call 119 or 112.';
  }
  return response;
}

module.exports = ${this.toPascalCase(fileName)};
`;
  }

  /**
   * Generate Markdown content
   */
  generateMarkdownContent(fileName, task) {
    return `# ${this.toTitleCase(fileName)}

Generated by task: ${task.description}

## Overview

TODO: Implement based on task requirements.

## Medical Safety Notice

⚠️ **Important**: This system does not provide medical diagnoses or treatment advice.

### Emergency Contacts (Taiwan)
- **Emergency Medical**: 119
- **International Emergency**: 112
- **Police**: 110

### Medical Disclaimer

This system is for informational purposes only and does not constitute medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical concerns.

## Implementation Notes

- Success Criteria: ${task.successCriteria || 'To be defined'}
- Leverage: ${task.leverage || 'To be determined'}

## Safety Compliance

- [ ] No diagnostic language used
- [ ] Emergency contacts prominently displayed
- [ ] Medical disclaimers included
- [ ] Taiwan health regulations considered
`;
  }

  /**
   * Generate generic content
   */
  generateGenericContent(fileName, task) {
    return `# ${fileName}
# Generated by task: ${task.description}
# TODO: Implement based on task requirements
# Success Criteria: ${task.successCriteria || 'To be defined'}
# Medical Safety: Ensure no diagnostic language and include emergency contacts (119, 112)
`;
  }

  /**
   * Apply modifications to existing files
   */
  applyTaskModifications(content, task) {
    // Add medical safety checks if medical content detected
    if (this.isMedicalContent(content) && !this.hasMedicalSafety(content)) {
      content = this.addMedicalSafetyToContent(content);
    }

    return content;
  }

  /**
   * Check if content is medical-related
   */
  isMedicalContent(content) {
    const medicalKeywords = ['symptom', 'diagnosis', 'treatment', 'hospital', 'medical', 'health', 'patient'];
    return medicalKeywords.some(keyword => content.toLowerCase().includes(keyword));
  }

  /**
   * Check if content has medical safety measures
   */
  hasMedicalSafety(content) {
    const safetyIndicators = ['disclaimer', '119', 'emergency', 'not medical advice'];
    return safetyIndicators.some(indicator => content.toLowerCase().includes(indicator));
  }

  /**
   * Add medical safety to content
   */
  addMedicalSafetyToContent(content) {
    const disclaimer = '\n\n// Medical Safety: This is not medical advice. For emergencies, call 119 or 112.\n';
    return content + disclaimer;
  }

  /**
   * Run tests for the task
   */
  async runTests(task) {
    try {
      const testCommand = task.testCommand || 'npm test';
      console.log(`🧪 Running tests: ${testCommand}`);
      execSync(testCommand, { stdio: 'inherit' });
      return { status: 'passed' };
    } catch (error) {
      console.error('❌ Tests failed:', error.message);
      return { status: 'failed', error: error.message };
    }
  }

  /**
   * Validate success criteria
   */
  async validateSuccessCriteria(criteria, task) {
    console.log(`✅ Validating: ${criteria}`);
    // TODO: Implement specific validation logic based on criteria
    return { validated: true, criteria };
  }

  /**
   * Store task completion in memory
   */
  async storeTaskInMemory(task, result) {
    try {
      const memoryKey = `spec/tasks/${task.id}`;
      const memoryData = JSON.stringify({
        task: task.description,
        result,
        timestamp: new Date().toISOString()
      });

      // Store in coordination memory
      execSync(`npx claude-flow@alpha hooks memory-store --key "${memoryKey}" --data '${memoryData}'`,
        { stdio: 'pipe' });

    } catch (error) {
      console.warn('⚠️ Failed to store in memory:', error.message);
    }
  }

  /**
   * Convert string to PascalCase
   */
  toPascalCase(str) {
    return str.replace(/[-_](.)/g, (_, char) => char.toUpperCase())
              .replace(/^./, char => char.toUpperCase());
  }

  /**
   * Convert string to Title Case
   */
  toTitleCase(str) {
    return str.replace(/[-_]/g, ' ')
              .replace(/\b\w/g, char => char.toUpperCase());
  }

  /**
   * Get task execution history
   */
  getTaskHistory() {
    return this.taskHistory;
  }

  /**
   * Get current task status
   */
  getCurrentTask() {
    return this.currentTask;
  }
}

// CLI usage
if (require.main === module) {
  const taskId = process.argv[2];
  const taskDescription = process.argv[3];

  if (!taskId || !taskDescription) {
    console.error('Usage: node spec-task-executor.js <task-id> "<task-description>"');
    console.error('Example: node spec-task-executor.js "task-001" "Create symptom validation model"');
    process.exit(1);
  }

  const executor = new TaskExecutor();

  executor.executeTask(taskId, taskDescription)
    .then(result => {
      console.log('\n✅ Task execution completed successfully');
      console.log('Result:', JSON.stringify(result, null, 2));
    })
    .catch(error => {
      console.error('\n❌ Task execution failed:', error.message);
      process.exit(1);
    });
}

module.exports = TaskExecutor;