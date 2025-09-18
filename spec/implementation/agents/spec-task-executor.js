/**
 * Spec Task Executor Agent
 * Implementation specialist for executing individual spec tasks
 * Focuses on clean, tested code following medical AI project conventions
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class SpecTaskExecutor {
  constructor(config = {}) {
    this.config = {
      projectRoot: config.projectRoot || process.cwd(),
      testFirst: config.testFirst !== false, // Default to TDD
      medicalSafety: config.medicalSafety !== false, // Default medical safety checks
      taiwanCompliance: config.taiwanCompliance !== false, // Default Taiwan compliance
      language: config.language || 'zh-TW',
      emergencyNumbers: ['119', '110', '112', '113', '165'],
      ...config
    };

    this.taskId = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    this.sessionId = `spec-impl-${Date.now()}`;
    this.memoryKey = `spec/implementation/${this.taskId}`;
  }

  /**
   * Execute a specification task with full TDD workflow
   */
  async executeTask(taskSpec) {
    await this.initializeTask(taskSpec);

    try {
      // Phase 1: Analysis and Planning
      const analysis = await this.analyzeTask(taskSpec);
      await this.storeProgress('analysis', analysis);

      // Phase 2: Test Design (TDD First)
      if (this.config.testFirst) {
        const testPlan = await this.designTests(taskSpec, analysis);
        await this.storeProgress('test_plan', testPlan);
        await this.implementTests(testPlan);
      }

      // Phase 3: Implementation
      const implementation = await this.implementTask(taskSpec, analysis);
      await this.storeProgress('implementation', implementation);

      // Phase 4: Validation
      const validation = await this.validateImplementation(taskSpec, implementation);
      await this.storeProgress('validation', validation);

      // Phase 5: Integration
      const integration = await this.integrateImplementation(implementation);
      await this.storeProgress('integration', integration);

      return await this.completeTask(taskSpec, implementation, validation);

    } catch (error) {
      await this.handleError(error);
      throw error;
    }
  }

  /**
   * Initialize task execution with coordination hooks
   */
  async initializeTask(taskSpec) {
    await this.runHook('pre-task', {
      description: `Implementing: ${taskSpec.title}`,
      taskId: this.taskId,
      sessionId: this.sessionId
    });

    await this.runHook('session-restore', {
      sessionId: this.sessionId
    });

    // Store initial task state
    await this.storeInMemory({
      task: taskSpec,
      status: 'initialized',
      startTime: new Date().toISOString(),
      phase: 'initialization'
    });
  }

  /**
   * Analyze task requirements and constraints
   */
  async analyzeTask(taskSpec) {
    const analysis = {
      requirements: this.extractRequirements(taskSpec),
      medicalSafety: this.analyzeMedicalSafety(taskSpec),
      taiwanCompliance: this.analyzeTaiwanCompliance(taskSpec),
      technicalConstraints: this.analyzeTechnicalConstraints(taskSpec),
      testStrategy: this.planTestStrategy(taskSpec),
      riskAssessment: this.assessRisks(taskSpec)
    };

    // Apply medical AI specific analysis
    if (this.isMedicalTask(taskSpec)) {
      analysis.medicalValidation = {
        emergencyKeywords: this.identifyEmergencyKeywords(taskSpec),
        disclaimerRequired: true,
        privacyCompliance: this.assessPrivacyRequirements(taskSpec),
        regulatoryCompliance: ['PDPA', 'MOHW_guidelines']
      };
    }

    return analysis;
  }

  /**
   * Design comprehensive test suite
   */
  async designTests(taskSpec, analysis) {
    const testPlan = {
      unitTests: this.designUnitTests(taskSpec, analysis),
      integrationTests: this.designIntegrationTests(taskSpec, analysis),
      e2eTests: this.designE2ETests(taskSpec, analysis),
      medicalSafetyTests: this.designMedicalSafetyTests(taskSpec, analysis),
      complianceTests: this.designComplianceTests(taskSpec, analysis)
    };

    // Taiwan-specific test requirements
    if (this.config.taiwanCompliance) {
      testPlan.taiwanTests = {
        languageTests: this.designLanguageTests(), // zh-TW validation
        emergencyNumberTests: this.designEmergencyTests(),
        gdprComplianceTests: this.designPDPATests(),
        localizationTests: this.designLocalizationTests()
      };
    }

    return testPlan;
  }

  /**
   * Implement tests first (TDD approach)
   */
  async implementTests(testPlan) {
    for (const [testType, tests] of Object.entries(testPlan)) {
      if (Array.isArray(tests)) {
        for (const test of tests) {
          await this.writeTestFile(test);
          await this.runHook('post-edit', {
            file: test.filePath,
            memoryKey: `${this.memoryKey}/tests/${testType}`
          });
        }
      }
    }

    // Verify tests fail initially (Red phase of TDD)
    const testResults = await this.runTests();
    if (testResults.allPassed) {
      throw new Error('Tests should fail initially in TDD - check test implementation');
    }

    await this.storeProgress('tests_implemented', {
      testCount: this.countTests(testPlan),
      initialResults: testResults
    });
  }

  /**
   * Implement the actual task functionality
   */
  async implementTask(taskSpec, analysis) {
    const implementation = {
      files: [],
      functions: [],
      classes: [],
      apis: [],
      configurations: []
    };

    // Generate implementation based on task type
    switch (taskSpec.type) {
      case 'api_endpoint':
        implementation.apis = await this.implementApiEndpoints(taskSpec, analysis);
        break;
      case 'service':
        implementation.services = await this.implementServices(taskSpec, analysis);
        break;
      case 'model':
        implementation.models = await this.implementModels(taskSpec, analysis);
        break;
      case 'validator':
        implementation.validators = await this.implementValidators(taskSpec, analysis);
        break;
      case 'middleware':
        implementation.middleware = await this.implementMiddleware(taskSpec, analysis);
        break;
      default:
        implementation.components = await this.implementGeneric(taskSpec, analysis);
    }

    // Apply medical AI patterns
    if (this.isMedicalTask(taskSpec)) {
      implementation = await this.applyMedicalPatterns(implementation, analysis);
    }

    // Apply Taiwan localization
    if (this.config.taiwanCompliance) {
      implementation = await this.applyTaiwanLocalization(implementation);
    }

    return implementation;
  }

  /**
   * Validate implementation against requirements
   */
  async validateImplementation(taskSpec, implementation) {
    const validation = {
      codeQuality: await this.validateCodeQuality(implementation),
      testCoverage: await this.validateTestCoverage(),
      medicalSafety: await this.validateMedicalSafety(implementation),
      taiwanCompliance: await this.validateTaiwanCompliance(implementation),
      performance: await this.validatePerformance(implementation),
      security: await this.validateSecurity(implementation)
    };

    // Run all tests to ensure implementation is correct (Green phase of TDD)
    const testResults = await this.runTests();
    validation.testResults = testResults;

    if (!testResults.allPassed) {
      throw new Error('Implementation failed tests - TDD cycle incomplete');
    }

    return validation;
  }

  /**
   * Integrate implementation with existing codebase
   */
  async integrateImplementation(implementation) {
    const integration = {
      conflicts: await this.checkConflicts(implementation),
      dependencies: await this.updateDependencies(implementation),
      configurations: await this.updateConfigurations(implementation),
      documentation: await this.updateDocumentation(implementation)
    };

    // Run integration tests
    const integrationResults = await this.runIntegrationTests();
    integration.testResults = integrationResults;

    return integration;
  }

  /**
   * Complete task and cleanup
   */
  async completeTask(taskSpec, implementation, validation) {
    const completion = {
      taskId: this.taskId,
      status: 'completed',
      endTime: new Date().toISOString(),
      implementation,
      validation,
      metrics: await this.calculateMetrics()
    };

    await this.storeProgress('completion', completion);

    await this.runHook('post-task', {
      taskId: this.taskId,
      success: true,
      metrics: completion.metrics
    });

    await this.runHook('notify', {
      message: `Task completed: ${taskSpec.title}`,
      type: 'success',
      details: completion
    });

    await this.runHook('session-end', {
      sessionId: this.sessionId,
      exportMetrics: true
    });

    return completion;
  }

  /**
   * Medical safety specific implementations
   */
  isMedicalTask(taskSpec) {
    const medicalKeywords = [
      'symptom', 'diagnosis', 'triage', 'hospital', 'emergency',
      'medical', 'health', 'patient', 'doctor', 'treatment'
    ];

    const content = (taskSpec.title + ' ' + taskSpec.description).toLowerCase();
    return medicalKeywords.some(keyword => content.includes(keyword));
  }

  async applyMedicalPatterns(implementation, analysis) {
    // Add emergency response patterns
    if (analysis.medicalValidation?.emergencyKeywords.length > 0) {
      implementation.emergencyHandlers = await this.addEmergencyHandlers();
    }

    // Add medical disclaimers
    implementation.disclaimers = await this.addMedicalDisclaimers();

    // Add privacy protection
    implementation.privacyMiddleware = await this.addPrivacyProtection();

    return implementation;
  }

  async validateMedicalSafety(implementation) {
    return {
      emergencyHandling: await this.checkEmergencyHandling(implementation),
      disclaimers: await this.checkDisclaimers(implementation),
      privacyProtection: await this.checkPrivacyProtection(implementation),
      noMedicalDiagnosis: await this.checkNoDiagnosis(implementation)
    };
  }

  /**
   * Taiwan compliance specific implementations
   */
  async applyTaiwanLocalization(implementation) {
    // Ensure zh-TW language
    implementation.localization = {
      language: 'zh-TW',
      region: 'TW',
      emergencyNumbers: this.config.emergencyNumbers,
      timeZone: 'Asia/Taipei'
    };

    // Add PDPA compliance
    implementation.pdpaCompliance = await this.addPDPACompliance();

    return implementation;
  }

  async validateTaiwanCompliance(implementation) {
    return {
      language: await this.checkLanguageCompliance(implementation),
      emergencyNumbers: await this.checkEmergencyNumbers(implementation),
      pdpaCompliance: await this.checkPDPACompliance(implementation),
      localization: await this.checkLocalization(implementation)
    };
  }

  /**
   * Utility methods for coordination and storage
   */
  async runHook(hookName, params = {}) {
    try {
      const result = await this.execCommand(`npx claude-flow@alpha hooks ${hookName}`, params);
      return result;
    } catch (error) {
      console.warn(`Hook ${hookName} failed:`, error.message);
      return null;
    }
  }

  async storeInMemory(data) {
    try {
      await this.runHook('post-edit', {
        memoryKey: this.memoryKey,
        data: JSON.stringify(data, null, 2)
      });
    } catch (error) {
      console.warn('Failed to store in memory:', error.message);
    }
  }

  async storeProgress(phase, data) {
    const progressData = {
      taskId: this.taskId,
      phase,
      timestamp: new Date().toISOString(),
      data
    };

    await this.storeInMemory(progressData);
  }

  async execCommand(command, params = {}) {
    return new Promise((resolve, reject) => {
      const paramString = Object.entries(params)
        .map(([key, value]) => `--${key} "${value}"`)
        .join(' ');

      const fullCommand = `${command} ${paramString}`;

      const child = spawn('cmd', ['/c', fullCommand], {
        cwd: this.config.projectRoot,
        stdio: 'pipe'
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        if (code === 0) {
          resolve(stdout);
        } else {
          reject(new Error(stderr || `Command failed with code ${code}`));
        }
      });
    });
  }

  async handleError(error) {
    await this.storeProgress('error', {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });

    await this.runHook('notify', {
      message: `Task failed: ${error.message}`,
      type: 'error'
    });
  }

  // Placeholder methods for specific implementations
  extractRequirements(taskSpec) { return taskSpec.requirements || []; }
  analyzeMedicalSafety(taskSpec) { return {}; }
  analyzeTaiwanCompliance(taskSpec) { return {}; }
  analyzeTechnicalConstraints(taskSpec) { return {}; }
  planTestStrategy(taskSpec) { return {}; }
  assessRisks(taskSpec) { return []; }
  identifyEmergencyKeywords(taskSpec) { return []; }
  assessPrivacyRequirements(taskSpec) { return {}; }
  designUnitTests(taskSpec, analysis) { return []; }
  designIntegrationTests(taskSpec, analysis) { return []; }
  designE2ETests(taskSpec, analysis) { return []; }
  designMedicalSafetyTests(taskSpec, analysis) { return []; }
  designComplianceTests(taskSpec, analysis) { return []; }
  designLanguageTests() { return []; }
  designEmergencyTests() { return []; }
  designPDPATests() { return []; }
  designLocalizationTests() { return []; }
  async writeTestFile(test) { }
  async runTests() { return { allPassed: false, results: [] }; }
  countTests(testPlan) { return 0; }
  async implementApiEndpoints(taskSpec, analysis) { return []; }
  async implementServices(taskSpec, analysis) { return []; }
  async implementModels(taskSpec, analysis) { return []; }
  async implementValidators(taskSpec, analysis) { return []; }
  async implementMiddleware(taskSpec, analysis) { return []; }
  async implementGeneric(taskSpec, analysis) { return []; }
  async addEmergencyHandlers() { return []; }
  async addMedicalDisclaimers() { return []; }
  async addPrivacyProtection() { return []; }
  async addPDPACompliance() { return []; }
  async validateCodeQuality(implementation) { return {}; }
  async validateTestCoverage() { return {}; }
  async validatePerformance(implementation) { return {}; }
  async validateSecurity(implementation) { return {}; }
  async checkConflicts(implementation) { return []; }
  async updateDependencies(implementation) { return []; }
  async updateConfigurations(implementation) { return []; }
  async updateDocumentation(implementation) { return []; }
  async runIntegrationTests() { return { allPassed: true, results: [] }; }
  async calculateMetrics() { return {}; }
  async checkEmergencyHandling(implementation) { return true; }
  async checkDisclaimers(implementation) { return true; }
  async checkPrivacyProtection(implementation) { return true; }
  async checkNoDiagnosis(implementation) { return true; }
  async checkLanguageCompliance(implementation) { return true; }
  async checkEmergencyNumbers(implementation) { return true; }
  async checkPDPACompliance(implementation) { return true; }
  async checkLocalization(implementation) { return true; }
}

module.exports = SpecTaskExecutor;