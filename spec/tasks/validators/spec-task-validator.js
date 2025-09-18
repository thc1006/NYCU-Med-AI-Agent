#!/usr/bin/env node

/**
 * Comprehensive Task Validator for Medical AI Agent
 * Validates task atomicity, agent-friendliness, and implementability
 */

const fs = require('fs');
const path = require('path');

class TaskValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.strengths = [];
    this.templatePath = path.join(__dirname, '..', 'templates', 'tasks-template.md');
  }

  /**
   * Main validation entry point
   */
  async validateTaskDocument(taskFilePath) {
    console.log(`🔍 Validating tasks document: ${taskFilePath}`);

    if (!fs.existsSync(taskFilePath)) {
      throw new Error(`Task file not found: ${taskFilePath}`);
    }

    const taskContent = fs.readFileSync(taskFilePath, 'utf-8');
    const templateContent = this.loadTemplate();

    // Run all validation checks
    this.validateTemplateCompliance(taskContent, templateContent);
    this.validateAtomicity(taskContent);
    this.validateAgentFriendliness(taskContent);
    this.validateMedicalSafety(taskContent);
    this.validateTaiwanCompliance(taskContent);
    this.validateRequirementsTraceability(taskContent, taskFilePath);

    return this.generateReport();
  }

  /**
   * Load template for comparison
   */
  loadTemplate() {
    if (!fs.existsSync(this.templatePath)) {
      this.warnings.push('Template file not found - cannot validate template compliance');
      return '';
    }
    return fs.readFileSync(this.templatePath, 'utf-8');
  }

  /**
   * Validate document structure against template
   */
  validateTemplateCompliance(content, template) {
    const requiredSections = [
      'Task Overview',
      'Steering Document Compliance',
      'Atomic Task Requirements',
      'Task Format Guidelines',
      'Tasks'
    ];

    requiredSections.forEach(section => {
      if (!content.includes(section)) {
        this.errors.push(`Missing required template section: ${section}`);
      }
    });

    // Check checkbox format
    const checkboxPattern = /^-\s*\[\s*\]\s*\d+\.\s+.+$/gm;
    const checkboxes = content.match(checkboxPattern);

    if (!checkboxes || checkboxes.length === 0) {
      this.errors.push('No properly formatted task checkboxes found (- [ ] Number. Description format)');
    } else {
      this.strengths.push(`Found ${checkboxes.length} properly formatted task checkboxes`);
    }
  }

  /**
   * Validate task atomicity requirements
   */
  validateAtomicity(content) {
    const tasks = this.extractTasks(content);

    tasks.forEach((task, index) => {
      // Check task description length
      if (task.description.length > 100) {
        this.warnings.push(`Task ${index + 1}: Description too long (${task.description.length} chars) - may not be atomic`);
      }

      // Check for broad terms that indicate non-atomic tasks
      const broadTerms = ['system', 'integration', 'complete', 'entire', 'all', 'comprehensive'];
      const foundBroadTerms = broadTerms.filter(term =>
        task.description.toLowerCase().includes(term)
      );

      if (foundBroadTerms.length > 0) {
        this.warnings.push(`Task ${index + 1}: Contains broad terms (${foundBroadTerms.join(', ')}) - may not be atomic`);
      }

      // Check for specific file references
      const filePatterns = [
        /\.js/g, /\.py/g, /\.ts/g, /\.jsx/g, /\.vue/g,
        /\.md/g, /\.json/g, /\.yml/g, /\.yaml/g
      ];

      const hasFileReference = filePatterns.some(pattern =>
        pattern.test(task.description)
      );

      if (!hasFileReference && !task.description.toLowerCase().includes('file')) {
        this.warnings.push(`Task ${index + 1}: No specific file references - may be too abstract`);
      }
    });

    if (tasks.length === 0) {
      this.errors.push('No tasks found in document');
    } else {
      this.strengths.push(`Found ${tasks.length} tasks for validation`);
    }
  }

  /**
   * Validate agent-friendliness
   */
  validateAgentFriendliness(content) {
    const tasks = this.extractTasks(content);

    tasks.forEach((task, index) => {
      // Check for clear action verbs
      const actionVerbs = ['create', 'implement', 'write', 'test', 'build', 'add', 'update', 'fix', 'refactor'];
      const hasActionVerb = actionVerbs.some(verb =>
        task.description.toLowerCase().includes(verb)
      );

      if (!hasActionVerb) {
        this.warnings.push(`Task ${index + 1}: No clear action verb - may be ambiguous for agents`);
      }

      // Check for measurable success criteria
      const successIndicators = ['return', 'response', 'status', 'test', 'validate', 'verify', 'ensure'];
      const hasCriteria = successIndicators.some(indicator =>
        task.description.toLowerCase().includes(indicator)
      );

      if (!hasCriteria) {
        this.warnings.push(`Task ${index + 1}: No clear success criteria - difficult to verify completion`);
      }

      // Check for requirement references
      const reqPattern = /REQ-\d+|requirement|spec/gi;
      if (!reqPattern.test(task.description)) {
        this.warnings.push(`Task ${index + 1}: No requirement references - lacks traceability`);
      }
    });
  }

  /**
   * Validate medical safety considerations
   */
  validateMedicalSafety(content) {
    const medicalKeywords = ['symptom', 'diagnosis', 'treatment', 'emergency', 'hospital', 'triage'];
    const safetyKeywords = ['disclaimer', '119', '112', 'emergency', 'professional medical advice'];

    const hasMedicalContent = medicalKeywords.some(keyword =>
      content.toLowerCase().includes(keyword)
    );

    if (hasMedicalContent) {
      const hasSafetyMeasures = safetyKeywords.some(keyword =>
        content.toLowerCase().includes(keyword)
      );

      if (!hasSafetyMeasures) {
        this.errors.push('Medical content detected but no safety measures (disclaimers, emergency numbers) found');
      } else {
        this.strengths.push('Medical safety measures detected in task descriptions');
      }

      // Check for diagnostic language
      const diagnosticTerms = ['diagnose', 'cure', 'treat', 'prescribe'];
      const hasDiagnostic = diagnosticTerms.some(term =>
        content.toLowerCase().includes(term)
      );

      if (hasDiagnostic) {
        this.errors.push('Tasks contain diagnostic language - medical AI should not provide diagnoses');
      }
    }
  }

  /**
   * Validate Taiwan-specific compliance
   */
  validateTaiwanCompliance(content) {
    const taiwanIndicators = ['taiwan', 'zh-tw', 'mohw', '119', '健保', 'pdpa'];
    const hasTasksWithTaiwanContext = taiwanIndicators.some(indicator =>
      content.toLowerCase().includes(indicator)
    );

    if (hasTasksWithTaiwanContext) {
      this.strengths.push('Taiwan-specific context detected in tasks');

      // Check for language specification
      if (content.includes('zh-TW') || content.includes('繁體中文')) {
        this.strengths.push('Chinese Traditional language specification found');
      }

      // Check for emergency numbers
      if (content.includes('119') || content.includes('112')) {
        this.strengths.push('Taiwan emergency numbers referenced in tasks');
      }
    } else {
      this.warnings.push('No Taiwan-specific considerations found in tasks');
    }
  }

  /**
   * Validate requirements traceability
   */
  validateRequirementsTraceability(content, taskFilePath) {
    const specDir = path.dirname(path.dirname(taskFilePath));
    const requirementsPath = path.join(specDir, 'requirements.md');
    const designPath = path.join(specDir, 'design.md');

    // Check if requirements exist
    if (fs.existsSync(requirementsPath)) {
      const reqContent = fs.readFileSync(requirementsPath, 'utf-8');
      const reqPattern = /REQ-\d+/g;
      const reqs = reqContent.match(reqPattern) || [];

      reqs.forEach(req => {
        if (!content.includes(req)) {
          this.warnings.push(`Requirement ${req} from requirements.md not covered by any task`);
        }
      });

      if (reqs.length > 0) {
        this.strengths.push(`Requirements traceability check completed for ${reqs.length} requirements`);
      }
    } else {
      this.warnings.push('No requirements.md found for traceability validation');
    }

    // Check design implementation
    if (fs.existsSync(designPath)) {
      this.strengths.push('Design document found for implementation validation');
    }
  }

  /**
   * Extract tasks from content
   */
  extractTasks(content) {
    const taskPattern = /^-\s*\[\s*\]\s*(\d+)\.\s+(.+)$/gm;
    const tasks = [];
    let match;

    while ((match = taskPattern.exec(content)) !== null) {
      tasks.push({
        number: parseInt(match[1]),
        description: match[2].trim()
      });
    }

    return tasks;
  }

  /**
   * Generate validation report
   */
  generateReport() {
    const errorCount = this.errors.length;
    const warningCount = this.warnings.length;

    let rating = 'PASS';
    if (errorCount > 0) {
      rating = 'MAJOR_ISSUES';
    } else if (warningCount > 3) {
      rating = 'NEEDS_IMPROVEMENT';
    }

    return {
      rating,
      errors: this.errors,
      warnings: this.warnings,
      strengths: this.strengths,
      summary: {
        errorCount,
        warningCount,
        strengthCount: this.strengths.length
      }
    };
  }

  /**
   * Format report for console output
   */
  static formatReport(report) {
    const { rating, errors, warnings, strengths, summary } = report;

    let output = '\n';
    output += '='.repeat(60) + '\n';
    output += '📋 TASK VALIDATION REPORT\n';
    output += '='.repeat(60) + '\n';
    output += `Overall Rating: ${rating}\n`;
    output += `Errors: ${summary.errorCount} | Warnings: ${summary.warningCount} | Strengths: ${summary.strengthCount}\n\n`;

    if (errors.length > 0) {
      output += '❌ ERRORS:\n';
      errors.forEach((error, i) => output += `  ${i + 1}. ${error}\n`);
      output += '\n';
    }

    if (warnings.length > 0) {
      output += '⚠️  WARNINGS:\n';
      warnings.forEach((warning, i) => output += `  ${i + 1}. ${warning}\n`);
      output += '\n';
    }

    if (strengths.length > 0) {
      output += '✅ STRENGTHS:\n';
      strengths.forEach((strength, i) => output += `  ${i + 1}. ${strength}\n`);
      output += '\n';
    }

    output += '='.repeat(60) + '\n';

    return output;
  }
}

// CLI usage
if (require.main === module) {
  const taskFile = process.argv[2];

  if (!taskFile) {
    console.error('Usage: node spec-task-validator.js <task-file.md>');
    process.exit(1);
  }

  const validator = new TaskValidator();

  validator.validateTaskDocument(taskFile)
    .then(report => {
      console.log(TaskValidator.formatReport(report));
      process.exit(report.rating === 'MAJOR_ISSUES' ? 1 : 0);
    })
    .catch(error => {
      console.error('❌ Validation failed:', error.message);
      process.exit(1);
    });
}

module.exports = TaskValidator;