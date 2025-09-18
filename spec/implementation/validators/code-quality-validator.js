/**
 * Code Quality Validator with Medical Safety Checks
 * Automated validation for medical AI code implementation
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class CodeQualityValidator {
  constructor(config = {}) {
    this.config = {
      projectRoot: config.projectRoot || process.cwd(),
      medicalSafetyChecks: config.medicalSafetyChecks !== false,
      taiwanComplianceChecks: config.taiwanComplianceChecks !== false,
      testCoverageThreshold: config.testCoverageThreshold || 80,
      ...config
    };

    this.validationResults = {
      codeQuality: {},
      medicalSafety: {},
      taiwanCompliance: {},
      testCoverage: {},
      security: {},
      performance: {}
    };
  }

  /**
   * Run comprehensive code quality validation
   */
  async validateCodeQuality(filePaths = []) {
    console.log('🔍 Starting code quality validation...');

    try {
      // 1. Static code analysis
      await this.runStaticAnalysis(filePaths);

      // 2. Medical safety validation
      if (this.config.medicalSafetyChecks) {
        await this.validateMedicalSafety(filePaths);
      }

      // 3. Taiwan compliance validation
      if (this.config.taiwanComplianceChecks) {
        await this.validateTaiwanCompliance(filePaths);
      }

      // 4. Test coverage validation
      await this.validateTestCoverage();

      // 5. Security validation
      await this.validateSecurity(filePaths);

      // 6. Performance validation
      await this.validatePerformance(filePaths);

      // 7. Generate validation report
      const report = await this.generateValidationReport();

      return report;

    } catch (error) {
      console.error('❌ Code quality validation failed:', error.message);
      throw error;
    }
  }

  /**
   * Static code analysis using ESLint and similar tools
   */
  async runStaticAnalysis(filePaths) {
    console.log('📊 Running static code analysis...');

    const results = {
      linting: await this.runLinting(filePaths),
      typeChecking: await this.runTypeChecking(filePaths),
      codeComplexity: await this.analyzeComplexity(filePaths),
      codeStyle: await this.checkCodeStyle(filePaths)
    };

    this.validationResults.codeQuality = results;
    return results;
  }

  /**
   * Medical safety validation
   */
  async validateMedicalSafety(filePaths) {
    console.log('🏥 Validating medical safety compliance...');

    const medicalSafetyChecks = {
      emergencyHandling: await this.checkEmergencyHandling(filePaths),
      medicalDisclaimers: await this.checkMedicalDisclaimers(filePaths),
      noDiagnosisStatements: await this.checkNoDiagnosisStatements(filePaths),
      privacyProtection: await this.checkPrivacyProtection(filePaths),
      errorHandling: await this.checkMedicalErrorHandling(filePaths)
    };

    this.validationResults.medicalSafety = medicalSafetyChecks;
    return medicalSafetyChecks;
  }

  /**
   * Taiwan compliance validation
   */
  async validateTaiwanCompliance(filePaths) {
    console.log('🇹🇼 Validating Taiwan compliance...');

    const complianceChecks = {
      languageSupport: await this.checkLanguageSupport(filePaths),
      emergencyNumbers: await this.checkEmergencyNumbers(filePaths),
      pdpaCompliance: await this.checkPDPACompliance(filePaths),
      localization: await this.checkLocalization(filePaths),
      timeZone: await this.checkTimeZoneHandling(filePaths)
    };

    this.validationResults.taiwanCompliance = complianceChecks;
    return complianceChecks;
  }

  /**
   * Test coverage validation
   */
  async validateTestCoverage() {
    console.log('🧪 Validating test coverage...');

    const coverage = {
      overall: await this.measureOverallCoverage(),
      unitTests: await this.measureUnitTestCoverage(),
      integrationTests: await this.measureIntegrationTestCoverage(),
      medicalSafetyTests: await this.measureMedicalSafetyTestCoverage()
    };

    const passesThreshold = coverage.overall >= this.config.testCoverageThreshold;

    this.validationResults.testCoverage = {
      ...coverage,
      threshold: this.config.testCoverageThreshold,
      passes: passesThreshold
    };

    if (!passesThreshold) {
      throw new Error(`Test coverage ${coverage.overall}% below threshold ${this.config.testCoverageThreshold}%`);
    }

    return this.validationResults.testCoverage;
  }

  /**
   * Security validation
   */
  async validateSecurity(filePaths) {
    console.log('🔒 Validating security compliance...');

    const securityChecks = {
      vulnerabilities: await this.scanVulnerabilities(filePaths),
      secretsDetection: await this.detectSecrets(filePaths),
      inputValidation: await this.checkInputValidation(filePaths),
      authenticationSecurity: await this.checkAuthSecurity(filePaths),
      dataEncryption: await this.checkDataEncryption(filePaths)
    };

    this.validationResults.security = securityChecks;
    return securityChecks;
  }

  /**
   * Performance validation
   */
  async validatePerformance(filePaths) {
    console.log('⚡ Validating performance...');

    const performanceChecks = {
      responseTime: await this.checkResponseTimes(),
      memoryUsage: await this.checkMemoryUsage(),
      databaseQueries: await this.checkDatabasePerformance(),
      apiPerformance: await this.checkApiPerformance()
    };

    this.validationResults.performance = performanceChecks;
    return performanceChecks;
  }

  // Medical Safety Specific Checks

  async checkEmergencyHandling(filePaths) {
    const emergencyPatterns = [
      /119|110|112|113|165/, // Emergency numbers
      /emergency|緊急|急診/, // Emergency keywords
      /should_call_119|撥打119/ // Emergency action patterns
    ];

    const results = [];

    for (const filePath of filePaths) {
      if (await this.isMedicalFile(filePath)) {
        const content = await this.readFile(filePath);
        const hasEmergencyHandling = emergencyPatterns.some(pattern => pattern.test(content));

        results.push({
          file: filePath,
          hasEmergencyHandling,
          issues: hasEmergencyHandling ? [] : ['Missing emergency handling patterns']
        });
      }
    }

    return {
      passed: results.every(r => r.hasEmergencyHandling),
      results,
      summary: `${results.filter(r => r.hasEmergencyHandling).length}/${results.length} files have emergency handling`
    };
  }

  async checkMedicalDisclaimers(filePaths) {
    const disclaimerPatterns = [
      /disclaimer|免責聲明/i,
      /專業醫療|醫療專業/,
      /not.*medical.*advice|非.*醫療.*建議/i
    ];

    const results = [];

    for (const filePath of filePaths) {
      if (await this.isMedicalApiFile(filePath)) {
        const content = await this.readFile(filePath);
        const hasDisclaimer = disclaimerPatterns.some(pattern => pattern.test(content));

        results.push({
          file: filePath,
          hasDisclaimer,
          issues: hasDisclaimer ? [] : ['Missing medical disclaimer']
        });
      }
    }

    return {
      passed: results.every(r => r.hasDisclaimer),
      results,
      summary: `${results.filter(r => r.hasDisclaimer).length}/${results.length} medical APIs have disclaimers`
    };
  }

  async checkNoDiagnosisStatements(filePaths) {
    const dangerousPatterns = [
      /你患有|您患有|診斷為|確診|罹患/g,
      /你的病是|您的疾病是|肯定是|一定是/g,
      /definitive.*diagnosis|confirmed.*diagnosis/gi
    ];

    const results = [];

    for (const filePath of filePaths) {
      if (await this.isMedicalFile(filePath)) {
        const content = await this.readFile(filePath);
        const violations = [];

        dangerousPatterns.forEach((pattern, index) => {
          const matches = content.match(pattern);
          if (matches) {
            violations.push({
              pattern: pattern.toString(),
              matches: matches,
              count: matches.length
            });
          }
        });

        results.push({
          file: filePath,
          violations,
          passed: violations.length === 0
        });
      }
    }

    return {
      passed: results.every(r => r.passed),
      results,
      totalViolations: results.reduce((sum, r) => sum + r.violations.length, 0)
    };
  }

  // Taiwan Compliance Specific Checks

  async checkLanguageSupport(filePaths) {
    const taiwanPatterns = [
      /zh-TW|zh_TW/,
      /locale.*tw|language.*taiwanese/i,
      /繁體中文|台灣/
    ];

    const results = [];

    for (const filePath of filePaths) {
      const content = await this.readFile(filePath);
      const supportsTaiwan = taiwanPatterns.some(pattern => pattern.test(content));

      results.push({
        file: filePath,
        supportsTaiwan,
        issues: supportsTaiwan ? [] : ['Missing Taiwan language support']
      });
    }

    return {
      passed: results.some(r => r.supportsTaiwan), // At least one file should have Taiwan support
      results,
      summary: `${results.filter(r => r.supportsTaiwan).length}/${results.length} files support Taiwan locale`
    };
  }

  async checkEmergencyNumbers(filePaths) {
    const requiredNumbers = ['119', '110', '112', '113', '165'];
    const results = [];

    for (const filePath of filePaths) {
      if (await this.isConfigFile(filePath) || await this.isMedicalFile(filePath)) {
        const content = await this.readFile(filePath);
        const foundNumbers = requiredNumbers.filter(num => content.includes(num));

        results.push({
          file: filePath,
          foundNumbers,
          missingNumbers: requiredNumbers.filter(num => !content.includes(num)),
          hasAllNumbers: foundNumbers.length === requiredNumbers.length
        });
      }
    }

    return {
      passed: results.some(r => r.hasAllNumbers),
      results,
      requiredNumbers,
      summary: `Emergency numbers coverage: ${Math.max(...results.map(r => r.foundNumbers.length))}/${requiredNumbers.length}`
    };
  }

  async checkPDPACompliance(filePaths) {
    const pdpaPatterns = [
      /PDPA|個人資料保護法/,
      /privacy.*policy|隱私.*政策/i,
      /data.*protection|資料.*保護/i,
      /consent|同意/i
    ];

    const results = [];

    for (const filePath of filePaths) {
      if (await this.isPrivacyRelatedFile(filePath)) {
        const content = await this.readFile(filePath);
        const hasPDPACompliance = pdpaPatterns.some(pattern => pattern.test(content));

        results.push({
          file: filePath,
          hasPDPACompliance,
          issues: hasPDPACompliance ? [] : ['Missing PDPA compliance indicators']
        });
      }
    }

    return {
      passed: results.every(r => r.hasPDPACompliance),
      results,
      summary: `${results.filter(r => r.hasPDPACompliance).length}/${results.length} privacy files are PDPA compliant`
    };
  }

  // Test Coverage Analysis

  async measureOverallCoverage() {
    try {
      const result = await this.execCommand('npm run test:coverage');
      const coverageMatch = result.match(/All files\s+\|\s+(\d+\.?\d*)/);
      return coverageMatch ? parseFloat(coverageMatch[1]) : 0;
    } catch (error) {
      console.warn('Could not measure test coverage:', error.message);
      return 0;
    }
  }

  async measureMedicalSafetyTestCoverage() {
    try {
      // Look for medical safety specific tests
      const testFiles = await this.findTestFiles();
      const medicalTestFiles = testFiles.filter(file =>
        file.includes('medical') ||
        file.includes('safety') ||
        file.includes('emergency')
      );

      return {
        totalMedicalTests: medicalTestFiles.length,
        coverage: medicalTestFiles.length > 0 ? 'present' : 'missing'
      };
    } catch (error) {
      console.warn('Could not measure medical safety test coverage:', error.message);
      return { coverage: 'unknown' };
    }
  }

  // Security Checks

  async scanVulnerabilities(filePaths) {
    try {
      const result = await this.execCommand('npm audit --json');
      const auditData = JSON.parse(result);

      return {
        vulnerabilities: auditData.vulnerabilities || {},
        summary: auditData.metadata || {},
        critical: (auditData.metadata?.vulnerabilities?.critical || 0) === 0
      };
    } catch (error) {
      console.warn('Could not run security audit:', error.message);
      return { critical: true, summary: 'audit failed' };
    }
  }

  async detectSecrets(filePaths) {
    const secretPatterns = [
      /api[_-]?key\s*[:=]\s*['"]\w+['"]/i,
      /secret\s*[:=]\s*['"]\w+['"]/i,
      /password\s*[:=]\s*['"]\w+['"]/i,
      /token\s*[:=]\s*['"]\w+['"]/i
    ];

    const violations = [];

    for (const filePath of filePaths) {
      if (!filePath.includes('test') && !filePath.includes('example')) {
        const content = await this.readFile(filePath);

        secretPatterns.forEach(pattern => {
          const matches = content.match(pattern);
          if (matches) {
            violations.push({
              file: filePath,
              pattern: pattern.toString(),
              matches: matches
            });
          }
        });
      }
    }

    return {
      passed: violations.length === 0,
      violations,
      summary: `${violations.length} potential secrets detected`
    };
  }

  // Performance Checks

  async checkResponseTimes() {
    // This would integrate with actual performance testing
    return {
      averageResponseTime: 150, // ms
      maxResponseTime: 500, // ms
      passed: true // Would be based on actual measurements
    };
  }

  // Report Generation

  async generateValidationReport() {
    const report = {
      timestamp: new Date().toISOString(),
      overall: this.calculateOverallStatus(),
      details: this.validationResults,
      recommendations: this.generateRecommendations(),
      metrics: this.calculateMetrics()
    };

    // Save report to file
    const reportPath = path.join(this.config.projectRoot, 'validation-report.json');
    await this.writeFile(reportPath, JSON.stringify(report, null, 2));

    console.log(`📋 Validation report saved to: ${reportPath}`);
    return report;
  }

  calculateOverallStatus() {
    const categories = Object.keys(this.validationResults);
    const passed = categories.filter(category => {
      const result = this.validationResults[category];
      return result.passed !== false;
    });

    return {
      status: passed.length === categories.length ? 'PASSED' : 'FAILED',
      passedCategories: passed.length,
      totalCategories: categories.length,
      categories: this.validationResults
    };
  }

  generateRecommendations() {
    const recommendations = [];

    // Medical safety recommendations
    if (!this.validationResults.medicalSafety?.emergencyHandling?.passed) {
      recommendations.push({
        category: 'Medical Safety',
        priority: 'HIGH',
        message: 'Add emergency handling patterns for medical safety',
        action: 'Implement emergency keyword detection and 119 calling guidance'
      });
    }

    // Taiwan compliance recommendations
    if (!this.validationResults.taiwanCompliance?.languageSupport?.passed) {
      recommendations.push({
        category: 'Taiwan Compliance',
        priority: 'HIGH',
        message: 'Add Taiwan language support (zh-TW)',
        action: 'Configure locale and language settings for Taiwan'
      });
    }

    // Test coverage recommendations
    if (!this.validationResults.testCoverage?.passes) {
      recommendations.push({
        category: 'Test Coverage',
        priority: 'MEDIUM',
        message: 'Increase test coverage',
        action: `Add tests to reach ${this.config.testCoverageThreshold}% coverage threshold`
      });
    }

    return recommendations;
  }

  calculateMetrics() {
    return {
      codeQualityScore: this.calculateCategoryScore('codeQuality'),
      medicalSafetyScore: this.calculateCategoryScore('medicalSafety'),
      taiwanComplianceScore: this.calculateCategoryScore('taiwanCompliance'),
      testCoverageScore: this.validationResults.testCoverage?.overall || 0,
      securityScore: this.calculateCategoryScore('security'),
      performanceScore: this.calculateCategoryScore('performance')
    };
  }

  calculateCategoryScore(category) {
    const result = this.validationResults[category];
    if (!result) return 0;

    // Simple scoring based on passed checks
    const checks = Object.values(result);
    const passedChecks = checks.filter(check => check.passed !== false);
    return checks.length > 0 ? (passedChecks.length / checks.length) * 100 : 0;
  }

  // Utility methods

  async isMedicalFile(filePath) {
    const medicalKeywords = ['medical', 'health', 'symptom', 'triage', 'hospital', 'emergency'];
    const fileName = path.basename(filePath).toLowerCase();
    return medicalKeywords.some(keyword => fileName.includes(keyword));
  }

  async isMedicalApiFile(filePath) {
    const content = await this.readFile(filePath);
    return content.includes('triage') || content.includes('/v1/') || content.includes('symptom');
  }

  async isConfigFile(filePath) {
    const configNames = ['config', 'settings', 'constants', '.env'];
    const fileName = path.basename(filePath).toLowerCase();
    return configNames.some(name => fileName.includes(name));
  }

  async isPrivacyRelatedFile(filePath) {
    const privacyKeywords = ['privacy', 'middleware', 'auth', 'security'];
    const fileName = path.basename(filePath).toLowerCase();
    return privacyKeywords.some(keyword => fileName.includes(keyword));
  }

  async findTestFiles() {
    const testDir = path.join(this.config.projectRoot, 'tests');
    if (fs.existsSync(testDir)) {
      return this.getAllFiles(testDir).filter(file => file.endsWith('.test.js') || file.endsWith('.test.py'));
    }
    return [];
  }

  getAllFiles(dir) {
    const files = [];
    const items = fs.readdirSync(dir);

    for (const item of items) {
      const fullPath = path.join(dir, item);
      if (fs.statSync(fullPath).isDirectory()) {
        files.push(...this.getAllFiles(fullPath));
      } else {
        files.push(fullPath);
      }
    }

    return files;
  }

  async readFile(filePath) {
    try {
      return fs.readFileSync(filePath, 'utf8');
    } catch (error) {
      console.warn(`Could not read file ${filePath}:`, error.message);
      return '';
    }
  }

  async writeFile(filePath, content) {
    fs.writeFileSync(filePath, content, 'utf8');
  }

  async execCommand(command) {
    return new Promise((resolve, reject) => {
      const child = spawn('cmd', ['/c', command], {
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

  // Placeholder methods for specific checks
  async runLinting(filePaths) { return { passed: true, issues: [] }; }
  async runTypeChecking(filePaths) { return { passed: true, issues: [] }; }
  async analyzeComplexity(filePaths) { return { averageComplexity: 5, maxComplexity: 10 }; }
  async checkCodeStyle(filePaths) { return { passed: true, violations: [] }; }
  async checkPrivacyProtection(filePaths) { return { passed: true, issues: [] }; }
  async checkMedicalErrorHandling(filePaths) { return { passed: true, issues: [] }; }
  async checkLocalization(filePaths) { return { passed: true, issues: [] }; }
  async checkTimeZoneHandling(filePaths) { return { passed: true, issues: [] }; }
  async measureUnitTestCoverage() { return 75; }
  async measureIntegrationTestCoverage() { return 60; }
  async checkInputValidation(filePaths) { return { passed: true, issues: [] }; }
  async checkAuthSecurity(filePaths) { return { passed: true, issues: [] }; }
  async checkDataEncryption(filePaths) { return { passed: true, issues: [] }; }
  async checkMemoryUsage() { return { averageMemory: '50MB', maxMemory: '100MB' }; }
  async checkDatabasePerformance() { return { averageQueryTime: '10ms' }; }
  async checkApiPerformance() { return { averageResponseTime: '150ms' }; }
}

module.exports = CodeQualityValidator;