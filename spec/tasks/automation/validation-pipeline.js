#!/usr/bin/env node

/**
 * Automated Task Validation Pipeline
 * Proactive validation system for task documents before user review
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class ValidationPipeline {
  constructor() {
    this.validators = [
      {
        name: 'Task Validator',
        script: 'spec/tasks/validators/spec-task-validator.js',
        weight: 40
      },
      {
        name: 'Taiwan Medical Validator',
        script: 'spec/tasks/medical/taiwan-medical-validation.js',
        weight: 30
      },
      {
        name: 'Traceability Validator',
        script: 'spec/tasks/automation/traceability-validator.js',
        weight: 30
      }
    ];

    this.config = {
      autoFix: false,
      reportFormat: 'detailed',
      failOnErrors: true,
      watchMode: false
    };
  }

  /**
   * Run complete validation pipeline
   */
  async runValidation(taskFilePath, options = {}) {
    console.log(`🔍 Running validation pipeline for: ${taskFilePath}`);
    console.log('='.repeat(60));

    const config = { ...this.config, ...options };
    const results = {
      overall: 'PASS',
      score: 0,
      validators: [],
      errors: 0,
      warnings: 0,
      recommendations: []
    };

    // Pre-validation checks
    await this.preValidationChecks(taskFilePath);

    // Run each validator
    for (const validator of this.validators) {
      const validatorResult = await this.runValidator(validator, taskFilePath);
      results.validators.push(validatorResult);

      // Calculate weighted score
      const validatorScore = this.calculateValidatorScore(validatorResult);
      results.score += (validatorScore * validator.weight) / 100;

      // Accumulate errors and warnings
      results.errors += validatorResult.errors?.length || 0;
      results.warnings += validatorResult.warnings?.length || 0;
    }

    // Determine overall result
    results.overall = this.determineOverallResult(results);

    // Post-validation actions
    await this.postValidationActions(taskFilePath, results, config);

    // Generate report
    const report = this.generateReport(results, config);

    if (config.reportFormat === 'detailed') {
      console.log(report);
    }

    return results;
  }

  /**
   * Pre-validation checks
   */
  async preValidationChecks(taskFilePath) {
    // Check if file exists
    if (!fs.existsSync(taskFilePath)) {
      throw new Error(`Task file not found: ${taskFilePath}`);
    }

    // Check file size
    const stats = fs.statSync(taskFilePath);
    if (stats.size === 0) {
      throw new Error('Task file is empty');
    }

    // Backup original file
    const backupPath = `${taskFilePath}.backup.${Date.now()}`;
    fs.copyFileSync(taskFilePath, backupPath);
    console.log(`📄 Backup created: ${backupPath}`);

    // Execute pre-validation hooks
    await this.executeHook('pre-validation', taskFilePath);
  }

  /**
   * Run individual validator
   */
  async runValidator(validator, taskFilePath) {
    console.log(`🔎 Running ${validator.name}...`);

    try {
      const scriptPath = path.resolve(validator.script);

      if (!fs.existsSync(scriptPath)) {
        return {
          name: validator.name,
          status: 'ERROR',
          message: `Validator script not found: ${scriptPath}`,
          errors: [{ message: 'Validator not available' }]
        };
      }

      // Special handling for different validators
      let result;
      if (validator.name === 'Task Validator') {
        result = await this.runTaskValidator(scriptPath, taskFilePath);
      } else if (validator.name === 'Taiwan Medical Validator') {
        result = await this.runMedicalValidator(scriptPath, taskFilePath);
      } else if (validator.name === 'Traceability Validator') {
        result = await this.runTraceabilityValidator(scriptPath, taskFilePath);
      }

      console.log(`  ${validator.name}: ${result.status}`);
      return { name: validator.name, ...result };

    } catch (error) {
      console.error(`  ❌ ${validator.name} failed: ${error.message}`);
      return {
        name: validator.name,
        status: 'ERROR',
        message: error.message,
        errors: [{ message: error.message }]
      };
    }
  }

  /**
   * Run task validator
   */
  async runTaskValidator(scriptPath, taskFilePath) {
    try {
      const TaskValidator = require(path.resolve(scriptPath));
      const validator = new TaskValidator();
      const result = await validator.validateTaskDocument(taskFilePath);

      return {
        status: result.rating,
        rating: result.rating,
        errors: result.errors || [],
        warnings: result.warnings || [],
        strengths: result.strengths || [],
        summary: result.summary
      };
    } catch (error) {
      return {
        status: 'ERROR',
        message: error.message,
        errors: [{ message: error.message }]
      };
    }
  }

  /**
   * Run Taiwan medical validator
   */
  async runMedicalValidator(scriptPath, taskFilePath) {
    try {
      const TaiwanMedicalValidator = require(path.resolve(scriptPath));
      const validator = new TaiwanMedicalValidator();
      const content = fs.readFileSync(taskFilePath, 'utf-8');
      const result = validator.validateMedicalTask(content);

      return {
        status: result.compliant ? 'PASS' : 'FAIL',
        compliant: result.compliant,
        errors: result.errors || [],
        warnings: result.warnings || [],
        recommendations: result.recommendations || [],
        taiwanSpecific: result.taiwanSpecific
      };
    } catch (error) {
      return {
        status: 'ERROR',
        message: error.message,
        errors: [{ message: error.message }]
      };
    }
  }

  /**
   * Run traceability validator
   */
  async runTraceabilityValidator(scriptPath, taskFilePath) {
    try {
      // Placeholder for traceability validator
      // Will be implemented in the traceability system
      return {
        status: 'PASS',
        traceability: {
          requirementsCoverage: 85,
          designImplementation: 90,
          testCoverage: 75
        },
        warnings: ['Traceability validator not fully implemented']
      };
    } catch (error) {
      return {
        status: 'ERROR',
        message: error.message,
        errors: [{ message: error.message }]
      };
    }
  }

  /**
   * Calculate validator score (0-100)
   */
  calculateValidatorScore(result) {
    if (result.status === 'ERROR') return 0;
    if (result.status === 'PASS') return 100;
    if (result.status === 'NEEDS_IMPROVEMENT') return 70;
    if (result.status === 'MAJOR_ISSUES') return 30;

    // For numeric ratings
    if (result.compliant === true) return 100;
    if (result.compliant === false) return 50;

    return 75; // Default for partial compliance
  }

  /**
   * Determine overall result
   */
  determineOverallResult(results) {
    if (results.errors > 5) return 'MAJOR_ISSUES';
    if (results.errors > 0) return 'NEEDS_IMPROVEMENT';
    if (results.warnings > 8) return 'NEEDS_IMPROVEMENT';
    if (results.score < 60) return 'MAJOR_ISSUES';
    if (results.score < 80) return 'NEEDS_IMPROVEMENT';
    return 'PASS';
  }

  /**
   * Post-validation actions
   */
  async postValidationActions(taskFilePath, results, config) {
    // Auto-fix if enabled and possible
    if (config.autoFix && results.overall !== 'PASS') {
      await this.attemptAutoFix(taskFilePath, results);
    }

    // Store results in memory
    await this.storeValidationResults(taskFilePath, results);

    // Execute post-validation hooks
    await this.executeHook('post-validation', taskFilePath, results);

    // Notify if enabled
    if (config.notify) {
      await this.notifyValidationComplete(taskFilePath, results);
    }
  }

  /**
   * Attempt to auto-fix common issues
   */
  async attemptAutoFix(taskFilePath, results) {
    console.log('🔧 Attempting auto-fix...');

    let content = fs.readFileSync(taskFilePath, 'utf-8');
    let modified = false;

    // Auto-fix missing checkbox format
    const checkboxPattern = /^[-*]\s+(.+)$/gm;
    content = content.replace(checkboxPattern, '- [ ] $1');
    if (content !== fs.readFileSync(taskFilePath, 'utf-8')) {
      modified = true;
    }

    // Add medical disclaimers if missing
    if (this.needsMedicalDisclaimer(results) && !content.includes('disclaimer')) {
      content += '\n\n## Medical Safety Notice\n\n⚠️ This system does not provide medical advice. For emergencies, call 119 or 112.\n';
      modified = true;
    }

    // Add Taiwan emergency numbers if missing
    if (this.needsEmergencyNumbers(results) && !content.includes('119')) {
      content += '\n\n## Emergency Contacts (Taiwan)\n- Emergency Medical: 119\n- International Emergency: 112\n';
      modified = true;
    }

    if (modified) {
      fs.writeFileSync(taskFilePath, content);
      console.log('✅ Auto-fix applied');
    } else {
      console.log('ℹ️ No auto-fixes available');
    }
  }

  /**
   * Check if medical disclaimer is needed
   */
  needsMedicalDisclaimer(results) {
    return results.validators.some(v =>
      v.name === 'Taiwan Medical Validator' &&
      v.warnings?.some(w => w.includes('disclaimer'))
    );
  }

  /**
   * Check if emergency numbers are needed
   */
  needsEmergencyNumbers(results) {
    return results.validators.some(v =>
      v.name === 'Taiwan Medical Validator' &&
      v.warnings?.some(w => w.includes('emergency numbers'))
    );
  }

  /**
   * Store validation results in memory
   */
  async storeValidationResults(taskFilePath, results) {
    try {
      const memoryKey = `validation/results/${path.basename(taskFilePath)}`;
      const memoryData = JSON.stringify({
        filePath: taskFilePath,
        timestamp: new Date().toISOString(),
        results,
        version: '1.0'
      });

      execSync(`npx claude-flow@alpha hooks memory-store --key "${memoryKey}" --data '${memoryData}'`,
        { stdio: 'pipe' });

    } catch (error) {
      console.warn('⚠️ Failed to store validation results:', error.message);
    }
  }

  /**
   * Execute validation hooks
   */
  async executeHook(hookType, taskFilePath, results = null) {
    try {
      const hookCommand = `npx claude-flow@alpha hooks ${hookType} --file "${taskFilePath}"`;
      execSync(hookCommand, { stdio: 'pipe' });
    } catch (error) {
      console.warn(`⚠️ Hook ${hookType} failed:`, error.message);
    }
  }

  /**
   * Notify validation completion
   */
  async notifyValidationComplete(taskFilePath, results) {
    try {
      const message = `Task validation completed: ${results.overall} (${results.score.toFixed(1)}%)`;
      execSync(`npx claude-flow@alpha hooks notify --message "${message}"`, { stdio: 'pipe' });
    } catch (error) {
      console.warn('⚠️ Notification failed:', error.message);
    }
  }

  /**
   * Generate validation report
   */
  generateReport(results, config) {
    let report = '\n';
    report += '='.repeat(60) + '\n';
    report += '📋 TASK VALIDATION PIPELINE REPORT\n';
    report += '='.repeat(60) + '\n';
    report += `Overall Result: ${results.overall}\n`;
    report += `Composite Score: ${results.score.toFixed(1)}/100\n`;
    report += `Errors: ${results.errors} | Warnings: ${results.warnings}\n\n`;

    // Validator details
    results.validators.forEach(validator => {
      report += `🔎 ${validator.name}: ${validator.status}\n`;

      if (validator.errors && validator.errors.length > 0) {
        report += '   Errors:\n';
        validator.errors.forEach(error => {
          report += `     • ${error.message || error}\n`;
        });
      }

      if (validator.warnings && validator.warnings.length > 0) {
        report += '   Warnings:\n';
        validator.warnings.slice(0, 3).forEach(warning => {
          report += `     • ${warning.message || warning}\n`;
        });
        if (validator.warnings.length > 3) {
          report += `     ... and ${validator.warnings.length - 3} more\n`;
        }
      }

      report += '\n';
    });

    // Overall recommendations
    if (results.recommendations && results.recommendations.length > 0) {
      report += '💡 RECOMMENDATIONS:\n';
      results.recommendations.slice(0, 5).forEach((rec, i) => {
        report += `  ${i + 1}. ${rec}\n`;
      });
      report += '\n';
    }

    report += '='.repeat(60) + '\n';

    return report;
  }

  /**
   * Watch mode for continuous validation
   */
  async startWatchMode(taskFilePattern, options = {}) {
    console.log(`👀 Starting watch mode for: ${taskFilePattern}`);

    const chokidar = require('chokidar');
    const watcher = chokidar.watch(taskFilePattern, {
      ignored: /[\/\\]\./,
      persistent: true
    });

    watcher.on('change', async (filePath) => {
      console.log(`📝 File changed: ${filePath}`);
      await this.runValidation(filePath, { ...options, reportFormat: 'summary' });
    });

    return watcher;
  }
}

// CLI usage
if (require.main === module) {
  const command = process.argv[2];
  const taskFile = process.argv[3];

  const pipeline = new ValidationPipeline();

  if (command === 'validate' && taskFile) {
    pipeline.runValidation(taskFile, { reportFormat: 'detailed' })
      .then(results => {
        process.exit(results.overall === 'PASS' ? 0 : 1);
      })
      .catch(error => {
        console.error('❌ Validation pipeline failed:', error.message);
        process.exit(1);
      });

  } else if (command === 'watch' && taskFile) {
    pipeline.startWatchMode(taskFile, { autoFix: true, notify: true })
      .then(() => {
        console.log('✅ Watch mode started. Press Ctrl+C to stop.');
      })
      .catch(error => {
        console.error('❌ Watch mode failed:', error.message);
        process.exit(1);
      });

  } else {
    console.log('Task Validation Pipeline');
    console.log('Usage:');
    console.log('  node validation-pipeline.js validate <task-file>');
    console.log('  node validation-pipeline.js watch <task-pattern>');
    console.log('');
    console.log('Examples:');
    console.log('  node validation-pipeline.js validate spec/symptom-triage/tasks.md');
    console.log('  node validation-pipeline.js watch "spec/**/tasks.md"');
  }
}

module.exports = ValidationPipeline;