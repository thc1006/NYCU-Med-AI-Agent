/**
 * Taiwan Compliance Validator
 * Comprehensive validation for Taiwan localization and PDPA compliance
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class TaiwanComplianceValidator {
  constructor(config = {}) {
    this.config = {
      projectRoot: config.projectRoot || process.cwd(),
      strictMode: config.strictMode !== false,
      validateFiles: config.validateFiles !== false,
      validateAPIs: config.validateAPIs !== false,
      validateData: config.validateData !== false,
      ...config
    };

    this.taiwanRequirements = {
      language: {
        required: 'zh-TW',
        forbidden: ['zh-CN', 'zh-Hans'],
        simplifiedChars: ['医', '疗', '药', '诊', '证', '护'],
        traditionalChars: ['醫', '療', '藥', '診', '證', '護']
      },
      emergencyNumbers: {
        required: ['119', '110', '112', '113', '165'],
        descriptions: {
          '119': '消防局救護車',
          '110': '警察局',
          '112': '行動電話國際緊急號碼',
          '113': '保護專線',
          '165': '反詐騙諮詢專線'
        }
      },
      pdpa: {
        requiredPolicies: ['collection', 'processing', 'usage', 'storage', 'deletion'],
        piiPatterns: {
          taiwanId: /\b[A-Z][12]\d{8}\b/,
          phone: /\b09\d{8}\b/,
          landline: /\b0\d{1,2}-?\d{6,8}\b/,
          email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/
        },
        maskingPatterns: {
          taiwanId: '[身分證號已遮罩]',
          phone: '[電話號碼已遮罩]',
          email: '[電子郵件已遮罩]'
        }
      },
      localization: {
        timeZone: 'Asia/Taipei',
        currency: 'TWD',
        dateFormat: 'YYYY/MM/DD',
        region: 'TW'
      }
    };

    this.validationResults = {
      language: {},
      emergencyNumbers: {},
      pdpa: {},
      localization: {},
      overall: {}
    };
  }

  /**
   * Run comprehensive Taiwan compliance validation
   */
  async validateTaiwanCompliance(filePaths = []) {
    console.log('🇹🇼 Starting Taiwan compliance validation...');

    try {
      // 1. Language compliance validation
      await this.validateLanguageCompliance(filePaths);

      // 2. Emergency numbers validation
      await this.validateEmergencyNumbers(filePaths);

      // 3. PDPA compliance validation
      await this.validatePDPACompliance(filePaths);

      // 4. Localization validation
      await this.validateLocalization(filePaths);

      // 5. Generate compliance report
      const report = await this.generateComplianceReport();

      return report;

    } catch (error) {
      console.error('❌ Taiwan compliance validation failed:', error.message);
      throw error;
    }
  }

  /**
   * Validate Traditional Chinese language compliance
   */
  async validateLanguageCompliance(filePaths) {
    console.log('📝 Validating Traditional Chinese language compliance...');

    const languageResults = {
      traditionalChineseUsage: [],
      simplifiedChineseViolations: [],
      localeConfiguration: [],
      encodingCompliance: []
    };

    for (const filePath of filePaths) {
      const content = await this.readFile(filePath);

      // Check for simplified Chinese characters
      const simplifiedViolations = this.checkSimplifiedCharacters(content, filePath);
      if (simplifiedViolations.length > 0) {
        languageResults.simplifiedChineseViolations.push(...simplifiedViolations);
      }

      // Check for proper locale configuration
      const localeCheck = this.checkLocaleConfiguration(content, filePath);
      if (localeCheck) {
        languageResults.localeConfiguration.push(localeCheck);
      }

      // Check for UTF-8 encoding compliance
      const encodingCheck = await this.checkEncodingCompliance(filePath);
      if (encodingCheck) {
        languageResults.encodingCompliance.push(encodingCheck);
      }

      // Check for Traditional Chinese usage
      const traditionalCheck = this.checkTraditionalChineseUsage(content, filePath);
      if (traditionalCheck) {
        languageResults.traditionalChineseUsage.push(traditionalCheck);
      }
    }

    this.validationResults.language = {
      passed: languageResults.simplifiedChineseViolations.length === 0,
      results: languageResults,
      summary: this.generateLanguageSummary(languageResults)
    };

    return this.validationResults.language;
  }

  /**
   * Validate emergency numbers compliance
   */
  async validateEmergencyNumbers(filePaths) {
    console.log('🚨 Validating emergency numbers compliance...');

    const emergencyResults = {
      requiredNumbersFound: [],
      missingNumbers: [],
      incorrectDescriptions: [],
      configurationFiles: []
    };

    const requiredNumbers = this.taiwanRequirements.emergencyNumbers.required;
    const expectedDescriptions = this.taiwanRequirements.emergencyNumbers.descriptions;

    for (const filePath of filePaths) {
      if (this.isConfigurationFile(filePath) || this.isMedicalFile(filePath)) {
        const content = await this.readFile(filePath);

        // Check for required emergency numbers
        const foundNumbers = requiredNumbers.filter(number => content.includes(number));
        const missingNumbers = requiredNumbers.filter(number => !content.includes(number));

        emergencyResults.requiredNumbersFound.push({
          file: filePath,
          found: foundNumbers,
          missing: missingNumbers
        });

        // Check for correct descriptions
        for (const [number, expectedDesc] of Object.entries(expectedDescriptions)) {
          if (content.includes(number)) {
            const hasCorrectDescription = content.includes(expectedDesc);
            if (!hasCorrectDescription) {
              emergencyResults.incorrectDescriptions.push({
                file: filePath,
                number,
                expected: expectedDesc,
                found: this.extractEmergencyNumberContext(content, number)
              });
            }
          }
        }

        emergencyResults.configurationFiles.push(filePath);
      }
    }

    const allNumbersConfigured = emergencyResults.requiredNumbersFound.some(
      result => result.missing.length === 0
    );

    this.validationResults.emergencyNumbers = {
      passed: allNumbersConfigured && emergencyResults.incorrectDescriptions.length === 0,
      results: emergencyResults,
      summary: this.generateEmergencyNumbersSummary(emergencyResults)
    };

    return this.validationResults.emergencyNumbers;
  }

  /**
   * Validate PDPA compliance
   */
  async validatePDPACompliance(filePaths) {
    console.log('🔒 Validating PDPA compliance...');

    const pdpaResults = {
      piiDetection: [],
      dataMasking: [],
      privacyPolicies: [],
      consentMechanisms: [],
      dataRetention: [],
      userRights: []
    };

    for (const filePath of filePaths) {
      const content = await this.readFile(filePath);

      // Check for PII patterns
      const piiViolations = this.detectPII(content, filePath);
      if (piiViolations.length > 0) {
        pdpaResults.piiDetection.push(...piiViolations);
      }

      // Check for data masking implementation
      const maskingCheck = this.checkDataMasking(content, filePath);
      if (maskingCheck) {
        pdpaResults.dataMasking.push(maskingCheck);
      }

      // Check for privacy policy references
      const privacyPolicyCheck = this.checkPrivacyPolicyReferences(content, filePath);
      if (privacyPolicyCheck) {
        pdpaResults.privacyPolicies.push(privacyPolicyCheck);
      }

      // Check for consent mechanisms
      const consentCheck = this.checkConsentMechanisms(content, filePath);
      if (consentCheck) {
        pdpaResults.consentMechanisms.push(consentCheck);
      }

      // Check for data retention policies
      const retentionCheck = this.checkDataRetentionPolicies(content, filePath);
      if (retentionCheck) {
        pdpaResults.dataRetention.push(retentionCheck);
      }

      // Check for user rights implementation
      const userRightsCheck = this.checkUserRights(content, filePath);
      if (userRightsCheck) {
        pdpaResults.userRights.push(userRightsCheck);
      }
    }

    const pdpaPassed = pdpaResults.piiDetection.length === 0 &&
                      pdpaResults.dataMasking.length > 0 &&
                      pdpaResults.privacyPolicies.length > 0;

    this.validationResults.pdpa = {
      passed: pdpaPassed,
      results: pdpaResults,
      summary: this.generatePDPASummary(pdpaResults)
    };

    return this.validationResults.pdpa;
  }

  /**
   * Validate localization settings
   */
  async validateLocalization(filePaths) {
    console.log('🌏 Validating localization settings...');

    const localizationResults = {
      timeZoneConfiguration: [],
      dateFormatting: [],
      currencyHandling: [],
      regionSettings: [],
      apiLocalization: []
    };

    for (const filePath of filePaths) {
      const content = await this.readFile(filePath);

      // Check time zone configuration
      const timeZoneCheck = this.checkTimeZoneConfiguration(content, filePath);
      if (timeZoneCheck) {
        localizationResults.timeZoneConfiguration.push(timeZoneCheck);
      }

      // Check date formatting
      const dateFormatCheck = this.checkDateFormatting(content, filePath);
      if (dateFormatCheck) {
        localizationResults.dateFormatting.push(dateFormatCheck);
      }

      // Check currency handling
      const currencyCheck = this.checkCurrencyHandling(content, filePath);
      if (currencyCheck) {
        localizationResults.currencyHandling.push(currencyCheck);
      }

      // Check region settings
      const regionCheck = this.checkRegionSettings(content, filePath);
      if (regionCheck) {
        localizationResults.regionSettings.push(regionCheck);
      }

      // Check API localization parameters
      const apiLocalizationCheck = this.checkAPILocalization(content, filePath);
      if (apiLocalizationCheck) {
        localizationResults.apiLocalization.push(apiLocalizationCheck);
      }
    }

    const localizationPassed = localizationResults.timeZoneConfiguration.length > 0 ||
                              localizationResults.regionSettings.length > 0;

    this.validationResults.localization = {
      passed: localizationPassed,
      results: localizationResults,
      summary: this.generateLocalizationSummary(localizationResults)
    };

    return this.validationResults.localization;
  }

  // Language compliance checking methods

  checkSimplifiedCharacters(content, filePath) {
    const violations = [];
    const simplifiedChars = this.taiwanRequirements.language.simplifiedChars;

    for (const char of simplifiedChars) {
      const regex = new RegExp(char, 'g');
      const matches = content.match(regex);
      if (matches) {
        violations.push({
          file: filePath,
          character: char,
          count: matches.length,
          suggestion: this.getTraditionalEquivalent(char)
        });
      }
    }

    return violations;
  }

  checkLocaleConfiguration(content, filePath) {
    const localePatterns = [
      /locale\s*[:=]\s*["']zh-TW["']/,
      /language\s*[:=]\s*["']zh-TW["']/,
      /lang\s*[:=]\s*["']zh-TW["']/
    ];

    const hasCorrectLocale = localePatterns.some(pattern => pattern.test(content));

    if (hasCorrectLocale) {
      return {
        file: filePath,
        status: 'compliant',
        localeFound: 'zh-TW'
      };
    }

    // Check for incorrect locales
    const incorrectPatterns = [
      /locale\s*[:=]\s*["']zh-CN["']/,
      /language\s*[:=]\s*["']zh-CN["']/,
      /lang\s*[:=]\s*["']zh-Hans["']/
    ];

    const hasIncorrectLocale = incorrectPatterns.some(pattern => pattern.test(content));

    if (hasIncorrectLocale) {
      return {
        file: filePath,
        status: 'violation',
        issue: 'Incorrect locale configuration found (zh-CN/zh-Hans)',
        recommendation: 'Use zh-TW for Taiwan Traditional Chinese'
      };
    }

    return null;
  }

  async checkEncodingCompliance(filePath) {
    try {
      // Check if file is properly UTF-8 encoded
      const buffer = fs.readFileSync(filePath);
      const content = buffer.toString('utf8');

      // Simple check - if we can read it as UTF-8 and it contains Chinese characters
      const hasChineseChars = /[\u4e00-\u9fff]/.test(content);

      if (hasChineseChars) {
        return {
          file: filePath,
          encoding: 'UTF-8',
          status: 'compliant',
          chineseCharacters: true
        };
      }

      return null;
    } catch (error) {
      return {
        file: filePath,
        status: 'error',
        issue: 'Could not verify UTF-8 encoding',
        error: error.message
      };
    }
  }

  checkTraditionalChineseUsage(content, filePath) {
    const traditionalChars = this.taiwanRequirements.language.traditionalChars;
    const hasTraditionalChars = traditionalChars.some(char => content.includes(char));

    if (hasTraditionalChars) {
      return {
        file: filePath,
        status: 'compliant',
        traditionalCharactersFound: traditionalChars.filter(char => content.includes(char))
      };
    }

    return null;
  }

  // Emergency numbers checking methods

  extractEmergencyNumberContext(content, number) {
    const lines = content.split('\n');
    const contextLines = [];

    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(number)) {
        contextLines.push(lines[i].trim());
      }
    }

    return contextLines;
  }

  // PDPA compliance checking methods

  detectPII(content, filePath) {
    const violations = [];
    const piiPatterns = this.taiwanRequirements.pdpa.piiPatterns;

    for (const [piiType, pattern] of Object.entries(piiPatterns)) {
      const matches = content.match(pattern);
      if (matches) {
        violations.push({
          file: filePath,
          type: piiType,
          matches: matches,
          count: matches.length,
          recommendation: `Mask ${piiType} with ${this.taiwanRequirements.pdpa.maskingPatterns[piiType]}`
        });
      }
    }

    return violations;
  }

  checkDataMasking(content, filePath) {
    const maskingPatterns = Object.values(this.taiwanRequirements.pdpa.maskingPatterns);
    const hasMasking = maskingPatterns.some(pattern => content.includes(pattern));

    if (hasMasking) {
      return {
        file: filePath,
        status: 'compliant',
        maskingImplemented: true,
        patterns: maskingPatterns.filter(pattern => content.includes(pattern))
      };
    }

    // Check for masking logic
    const maskingLogicPatterns = [
      /mask|遮罩/i,
      /sanitize|清理/i,
      /anonymize|匿名/i
    ];

    const hasMaskingLogic = maskingLogicPatterns.some(pattern => pattern.test(content));

    if (hasMaskingLogic) {
      return {
        file: filePath,
        status: 'partial',
        maskingLogicFound: true,
        recommendation: 'Ensure masking patterns are properly implemented'
      };
    }

    return null;
  }

  checkPrivacyPolicyReferences(content, filePath) {
    const privacyPatterns = [
      /privacy.*policy|隱私.*政策/i,
      /personal.*data.*protection|個人.*資料.*保護/i,
      /pdpa/i,
      /data.*collection|資料.*蒐集/i
    ];

    const hasPrivacyReferences = privacyPatterns.some(pattern => pattern.test(content));

    if (hasPrivacyReferences) {
      return {
        file: filePath,
        status: 'compliant',
        privacyReferencesFound: true
      };
    }

    return null;
  }

  checkConsentMechanisms(content, filePath) {
    const consentPatterns = [
      /consent|同意/i,
      /agree|接受/i,
      /opt.*in|選擇.*加入/i,
      /permission|許可/i
    ];

    const hasConsentMechanisms = consentPatterns.some(pattern => pattern.test(content));

    if (hasConsentMechanisms) {
      return {
        file: filePath,
        status: 'compliant',
        consentMechanismsFound: true
      };
    }

    return null;
  }

  checkDataRetentionPolicies(content, filePath) {
    const retentionPatterns = [
      /retention|保留/i,
      /delete.*after|刪除.*之後/i,
      /expir|到期/i,
      /storage.*period|儲存.*期間/i
    ];

    const hasRetentionPolicies = retentionPatterns.some(pattern => pattern.test(content));

    if (hasRetentionPolicies) {
      return {
        file: filePath,
        status: 'compliant',
        retentionPoliciesFound: true
      };
    }

    return null;
  }

  checkUserRights(content, filePath) {
    const userRightsPatterns = [
      /right.*access|查閱.*權利/i,
      /right.*delete|刪除.*權利/i,
      /right.*correct|更正.*權利/i,
      /data.*portability|資料.*可攜/i
    ];

    const hasUserRights = userRightsPatterns.some(pattern => pattern.test(content));

    if (hasUserRights) {
      return {
        file: filePath,
        status: 'compliant',
        userRightsFound: true
      };
    }

    return null;
  }

  // Localization checking methods

  checkTimeZoneConfiguration(content, filePath) {
    const timeZonePatterns = [
      /asia\/taipei/i,
      /timezone.*taiwan/i,
      /tz.*taiwan/i
    ];

    const hasCorrectTimeZone = timeZonePatterns.some(pattern => pattern.test(content));

    if (hasCorrectTimeZone) {
      return {
        file: filePath,
        status: 'compliant',
        timeZone: 'Asia/Taipei'
      };
    }

    return null;
  }

  checkDateFormatting(content, filePath) {
    const dateFormatPatterns = [
      /yyyy\/mm\/dd/i,
      /dateformat.*taiwan/i,
      /民國.*年/
    ];

    const hasCorrectDateFormat = dateFormatPatterns.some(pattern => pattern.test(content));

    if (hasCorrectDateFormat) {
      return {
        file: filePath,
        status: 'compliant',
        dateFormat: 'Taiwan format detected'
      };
    }

    return null;
  }

  checkCurrencyHandling(content, filePath) {
    const currencyPatterns = [
      /twd/i,
      /nt\$/i,
      /新台幣|新臺幣/,
      /currency.*taiwan/i
    ];

    const hasCorrectCurrency = currencyPatterns.some(pattern => pattern.test(content));

    if (hasCorrectCurrency) {
      return {
        file: filePath,
        status: 'compliant',
        currency: 'TWD'
      };
    }

    return null;
  }

  checkRegionSettings(content, filePath) {
    const regionPatterns = [
      /region.*tw/i,
      /country.*taiwan/i,
      /locale.*tw/i
    ];

    const hasCorrectRegion = regionPatterns.some(pattern => pattern.test(content));

    if (hasCorrectRegion) {
      return {
        file: filePath,
        status: 'compliant',
        region: 'TW'
      };
    }

    return null;
  }

  checkAPILocalization(content, filePath) {
    const apiLocalizationPatterns = [
      /language.*zh-tw/i,
      /region.*tw/i,
      /locale.*taiwan/i,
      /google.*api.*language.*zh/i
    ];

    const hasAPILocalization = apiLocalizationPatterns.some(pattern => pattern.test(content));

    if (hasAPILocalization) {
      return {
        file: filePath,
        status: 'compliant',
        apiLocalization: true
      };
    }

    return null;
  }

  // Report generation methods

  async generateComplianceReport() {
    const report = {
      timestamp: new Date().toISOString(),
      overall: this.calculateOverallCompliance(),
      categories: {
        language: this.validationResults.language,
        emergencyNumbers: this.validationResults.emergencyNumbers,
        pdpa: this.validationResults.pdpa,
        localization: this.validationResults.localization
      },
      recommendations: this.generateRecommendations(),
      summary: this.generateSummary()
    };

    // Save report
    const reportPath = path.join(this.config.projectRoot, 'taiwan-compliance-report.json');
    await this.writeFile(reportPath, JSON.stringify(report, null, 2));

    console.log(`📋 Taiwan compliance report saved to: ${reportPath}`);
    return report;
  }

  calculateOverallCompliance() {
    const categories = Object.values(this.validationResults);
    const passedCategories = categories.filter(category => category.passed);

    return {
      status: passedCategories.length === categories.length ? 'COMPLIANT' : 'NON_COMPLIANT',
      passedCategories: passedCategories.length,
      totalCategories: categories.length,
      compliancePercentage: categories.length > 0 ? (passedCategories.length / categories.length) * 100 : 0
    };
  }

  generateRecommendations() {
    const recommendations = [];

    if (!this.validationResults.language?.passed) {
      recommendations.push({
        category: 'Language',
        priority: 'HIGH',
        message: 'Implement Traditional Chinese (zh-TW) language support',
        actions: [
          'Replace simplified Chinese characters with traditional equivalents',
          'Configure locale settings to zh-TW',
          'Ensure UTF-8 encoding for all text files'
        ]
      });
    }

    if (!this.validationResults.emergencyNumbers?.passed) {
      recommendations.push({
        category: 'Emergency Numbers',
        priority: 'CRITICAL',
        message: 'Add Taiwan emergency contact numbers',
        actions: [
          'Configure all required emergency numbers (119, 110, 112, 113, 165)',
          'Add proper Chinese descriptions for each number',
          'Ensure emergency numbers are accessible in all medical contexts'
        ]
      });
    }

    if (!this.validationResults.pdpa?.passed) {
      recommendations.push({
        category: 'PDPA Compliance',
        priority: 'HIGH',
        message: 'Implement PDPA data protection measures',
        actions: [
          'Add PII detection and masking',
          'Implement privacy policy references',
          'Add user consent mechanisms',
          'Configure data retention policies'
        ]
      });
    }

    if (!this.validationResults.localization?.passed) {
      recommendations.push({
        category: 'Localization',
        priority: 'MEDIUM',
        message: 'Complete Taiwan localization settings',
        actions: [
          'Configure Asia/Taipei timezone',
          'Implement Taiwan date formatting',
          'Add TWD currency support',
          'Set region to TW for API calls'
        ]
      });
    }

    return recommendations;
  }

  generateSummary() {
    const totalChecks = Object.values(this.validationResults).length;
    const passedChecks = Object.values(this.validationResults).filter(result => result.passed).length;

    return {
      totalCategories: totalChecks,
      passedCategories: passedChecks,
      failedCategories: totalChecks - passedChecks,
      overallStatus: passedChecks === totalChecks ? 'COMPLIANT' : 'REQUIRES_ATTENTION',
      criticalIssues: this.identifyCriticalIssues(),
      nextSteps: this.generateNextSteps()
    };
  }

  // Summary generation methods

  generateLanguageSummary(results) {
    return `Language compliance: ${results.simplifiedChineseViolations.length === 0 ? 'PASSED' : 'FAILED'}. ` +
           `Found ${results.simplifiedChineseViolations.length} simplified character violations. ` +
           `Locale configuration found in ${results.localeConfiguration.length} files.`;
  }

  generateEmergencyNumbersSummary(results) {
    const totalRequired = this.taiwanRequirements.emergencyNumbers.required.length;
    const maxFound = Math.max(...results.requiredNumbersFound.map(r => r.found.length), 0);

    return `Emergency numbers: ${maxFound}/${totalRequired} required numbers configured. ` +
           `${results.incorrectDescriptions.length} description issues found.`;
  }

  generatePDPASummary(results) {
    return `PDPA compliance: ${results.piiDetection.length} PII violations detected. ` +
           `Data masking implemented in ${results.dataMasking.length} files. ` +
           `Privacy policies referenced in ${results.privacyPolicies.length} files.`;
  }

  generateLocalizationSummary(results) {
    const totalChecks = Object.values(results).reduce((sum, arr) => sum + arr.length, 0);
    return `Localization: ${totalChecks} compliance indicators found across all categories.`;
  }

  identifyCriticalIssues() {
    const critical = [];

    if (this.validationResults.emergencyNumbers && !this.validationResults.emergencyNumbers.passed) {
      critical.push('Missing Taiwan emergency numbers - critical for medical safety');
    }

    if (this.validationResults.pdpa?.results?.piiDetection?.length > 0) {
      critical.push('PII data detected without masking - PDPA violation');
    }

    if (this.validationResults.language?.results?.simplifiedChineseViolations?.length > 0) {
      critical.push('Simplified Chinese characters found - should use Traditional Chinese');
    }

    return critical;
  }

  generateNextSteps() {
    const steps = [];

    if (!this.validationResults.language?.passed) {
      steps.push('Fix language compliance issues first');
    }

    if (!this.validationResults.emergencyNumbers?.passed) {
      steps.push('Add emergency numbers configuration');
    }

    if (!this.validationResults.pdpa?.passed) {
      steps.push('Implement PII masking and privacy policies');
    }

    if (!this.validationResults.localization?.passed) {
      steps.push('Complete localization settings');
    }

    return steps;
  }

  // Utility methods

  getTraditionalEquivalent(simplifiedChar) {
    const mapping = {
      '医': '醫',
      '疗': '療',
      '药': '藥',
      '诊': '診',
      '证': '證',
      '护': '護'
    };

    return mapping[simplifiedChar] || simplifiedChar;
  }

  isConfigurationFile(filePath) {
    const configNames = ['config', 'settings', 'constants', '.env', 'package.json'];
    const fileName = path.basename(filePath).toLowerCase();
    return configNames.some(name => fileName.includes(name));
  }

  isMedicalFile(filePath) {
    const medicalKeywords = ['medical', 'health', 'symptom', 'triage', 'hospital', 'emergency'];
    const fileName = path.basename(filePath).toLowerCase();
    return medicalKeywords.some(keyword => fileName.includes(keyword));
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
}

module.exports = TaiwanComplianceValidator;