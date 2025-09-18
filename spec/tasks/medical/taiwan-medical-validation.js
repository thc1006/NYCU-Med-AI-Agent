#!/usr/bin/env node

/**
 * Taiwan-Specific Medical Validation Rules
 * Ensures tasks comply with Taiwan medical regulations and safety standards
 */

class TaiwanMedicalValidator {
  constructor() {
    this.emergencyNumbers = {
      '119': 'Fire Department / Emergency Medical Services',
      '112': 'International Emergency (GSM, no SIM required)',
      '110': 'Police',
      '113': 'Protection of Women and Children',
      '165': 'Anti-fraud Consultation Hotline'
    };

    this.prohibitedTerms = [
      'diagnose', 'diagnosis', 'cure', 'treat', 'prescribe', 'prescription',
      'medical advice', 'treatment plan', 'therapeutic recommendation'
    ];

    this.requiredElements = [
      'disclaimer', 'emergency contact', 'professional consultation',
      'not medical advice', '119', 'healthcare professional'
    ];

    this.mohwRegulations = [
      'PDPA compliance',
      'Medical Device Act',
      'Pharmaceutical Affairs Act',
      'Medical Care Act'
    ];
  }

  /**
   * Validate Taiwan medical compliance for tasks
   */
  validateMedicalTask(taskContent, taskMetadata = {}) {
    const results = {
      compliant: true,
      errors: [],
      warnings: [],
      recommendations: [],
      taiwanSpecific: {
        emergencyNumbers: false,
        languageSupport: false,
        mohwCompliance: false,
        pdpaCompliance: false
      }
    };

    // Check for prohibited diagnostic language
    this.checkProhibitedLanguage(taskContent, results);

    // Verify required safety elements
    this.checkRequiredSafetyElements(taskContent, results);

    // Validate Taiwan emergency numbers
    this.validateEmergencyNumbers(taskContent, results);

    // Check language support (Traditional Chinese)
    this.validateLanguageSupport(taskContent, results);

    // Verify MOHW regulation compliance
    this.validateMOHWCompliance(taskContent, results);

    // Check PDPA privacy compliance
    this.validatePDPACompliance(taskContent, results);

    // Medical device regulation compliance
    this.validateMedicalDeviceCompliance(taskContent, results);

    return results;
  }

  /**
   * Check for prohibited diagnostic language
   */
  checkProhibitedLanguage(content, results) {
    const lowerContent = content.toLowerCase();

    this.prohibitedTerms.forEach(term => {
      if (lowerContent.includes(term)) {
        results.compliant = false;
        results.errors.push(`Contains prohibited medical term: "${term}"`);
        results.recommendations.push(
          `Replace "${term}" with appropriate non-diagnostic language`
        );
      }
    });

    // Check for diagnostic patterns
    const diagnosticPatterns = [
      /you have/gi,
      /you are suffering from/gi,
      /this indicates/gi,
      /the diagnosis is/gi
    ];

    diagnosticPatterns.forEach(pattern => {
      if (pattern.test(content)) {
        results.compliant = false;
        results.errors.push('Contains diagnostic language pattern');
        results.recommendations.push(
          'Use informational language instead of diagnostic statements'
        );
      }
    });
  }

  /**
   * Verify required safety elements are present
   */
  checkRequiredSafetyElements(content, results) {
    const lowerContent = content.toLowerCase();
    const missingElements = [];

    this.requiredElements.forEach(element => {
      if (!lowerContent.includes(element)) {
        missingElements.push(element);
      }
    });

    if (missingElements.length > 0) {
      results.warnings.push(`Missing safety elements: ${missingElements.join(', ')}`);
      results.recommendations.push(
        'Include medical disclaimers and emergency contact information'
      );
    }
  }

  /**
   * Validate Taiwan emergency numbers are referenced
   */
  validateEmergencyNumbers(content, results) {
    const foundNumbers = [];

    Object.keys(this.emergencyNumbers).forEach(number => {
      if (content.includes(number)) {
        foundNumbers.push(number);
      }
    });

    if (foundNumbers.length > 0) {
      results.taiwanSpecific.emergencyNumbers = true;
      results.recommendations.push(
        `Good: Found Taiwan emergency numbers: ${foundNumbers.join(', ')}`
      );
    } else {
      results.warnings.push('No Taiwan emergency numbers (119, 112) referenced');
      results.recommendations.push(
        'Include Taiwan emergency contacts: 119 (Emergency Medical), 112 (International Emergency)'
      );
    }

    // Validate emergency number context
    if (content.includes('119') && !content.includes('emergency')) {
      results.warnings.push('119 mentioned without emergency context');
    }
  }

  /**
   * Validate Traditional Chinese language support
   */
  validateLanguageSupport(content, results) {
    const chinesePatterns = [
      /zh-tw/gi,
      /traditional chinese/gi,
      /繁體中文/gi,
      /正體中文/gi,
      /台灣/gi,
      /taiwan/gi
    ];

    const hasLanguageSupport = chinesePatterns.some(pattern => pattern.test(content));

    if (hasLanguageSupport) {
      results.taiwanSpecific.languageSupport = true;
      results.recommendations.push('Good: Traditional Chinese language support detected');
    } else {
      results.warnings.push('No Traditional Chinese (zh-TW) language support specified');
      results.recommendations.push(
        'Include zh-TW language specification for Taiwan localization'
      );
    }

    // Check for simplified Chinese (should be avoided)
    if (content.includes('zh-cn') || content.includes('simplified chinese')) {
      results.errors.push('Simplified Chinese detected - Taiwan uses Traditional Chinese');
      results.compliant = false;
    }
  }

  /**
   * Validate MOHW regulation compliance
   */
  validateMOHWCompliance(content, results) {
    const mohwIndicators = [
      'mohw', 'ministry of health', '衛生福利部',
      'health regulation', 'medical regulation',
      'taiwan health', 'nhi', 'national health insurance'
    ];

    const hasMOHWReference = mohwIndicators.some(indicator =>
      content.toLowerCase().includes(indicator)
    );

    if (hasMOHWReference) {
      results.taiwanSpecific.mohwCompliance = true;
      results.recommendations.push('Good: MOHW/Taiwan health system references found');
    } else {
      results.warnings.push('Consider referencing Taiwan health regulations (MOHW)');
    }

    // Check for specific regulation compliance
    this.mohwRegulations.forEach(regulation => {
      if (content.toLowerCase().includes(regulation.toLowerCase())) {
        results.recommendations.push(`Good: ${regulation} compliance referenced`);
      }
    });
  }

  /**
   * Validate PDPA privacy compliance
   */
  validatePDPACompliance(content, results) {
    const pdpaIndicators = [
      'pdpa', 'personal data protection',
      'privacy', 'data protection',
      'personal information', 'minimal data'
    ];

    const hasPDPAReference = pdpaIndicators.some(indicator =>
      content.toLowerCase().includes(indicator)
    );

    if (hasPDPAReference) {
      results.taiwanSpecific.pdpaCompliance = true;
      results.recommendations.push('Good: PDPA/privacy protection references found');
    } else {
      results.warnings.push('Consider Taiwan PDPA compliance for personal data handling');
      results.recommendations.push(
        'Include PDPA-compliant data handling practices'
      );
    }

    // Check for data minimization principles
    if (content.includes('minimal') || content.includes('necessary only')) {
      results.recommendations.push('Good: Data minimization principles referenced');
    }
  }

  /**
   * Validate medical device regulation compliance
   */
  validateMedicalDeviceCompliance(content, results) {
    const deviceIndicators = [
      'medical device', 'diagnostic tool', 'health monitoring',
      'medical software', 'health app'
    ];

    const hasDeviceContent = deviceIndicators.some(indicator =>
      content.toLowerCase().includes(indicator)
    );

    if (hasDeviceContent) {
      if (!content.toLowerCase().includes('not a medical device')) {
        results.warnings.push('Medical device content without proper disclaimers');
        results.recommendations.push(
          'Include "not a medical device" disclaimer for health-related software'
        );
      }

      if (!content.toLowerCase().includes('fda') && !content.toLowerCase().includes('tfda')) {
        results.recommendations.push(
          'Consider Taiwan FDA (TFDA) medical device regulations'
        );
      }
    }
  }

  /**
   * Generate Taiwan medical compliance checklist
   */
  generateComplianceChecklist() {
    return {
      emergencyNumbers: {
        title: 'Taiwan Emergency Numbers',
        required: ['119 (Emergency Medical)', '112 (International Emergency)'],
        optional: ['110 (Police)', '113 (Women/Children Protection)', '165 (Anti-fraud)']
      },
      medicalSafety: {
        title: 'Medical Safety Requirements',
        required: [
          'No diagnostic language',
          'Medical disclaimers',
          'Professional consultation advice',
          'Emergency contact prominence'
        ]
      },
      localization: {
        title: 'Taiwan Localization',
        required: [
          'Traditional Chinese (zh-TW) support',
          'Taiwan-specific content',
          'Local emergency services integration'
        ]
      },
      regulations: {
        title: 'Regulatory Compliance',
        required: [
          'PDPA privacy compliance',
          'MOHW health regulations',
          'Medical Device Act considerations',
          'Healthcare provider licensing awareness'
        ]
      }
    };
  }

  /**
   * Generate medical task template with Taiwan compliance
   */
  generateTaiwanMedicalTaskTemplate(featureName) {
    return `# ${featureName} - Taiwan Medical Compliance Task

## Medical Safety Requirements

### Prohibited Elements
- ❌ No diagnostic language ("diagnose", "cure", "treat")
- ❌ No medical advice provision
- ❌ No treatment recommendations

### Required Elements
- ✅ Medical disclaimers in all responses
- ✅ Taiwan emergency numbers (119, 112) prominently displayed
- ✅ Professional consultation guidance
- ✅ "Not medical advice" statements

## Taiwan-Specific Requirements

### Emergency Services Integration
- 119: Emergency Medical Services / Fire Department
- 112: International Emergency (GSM, no SIM required)
- Clear, accessible emergency contact interface

### Language Support
- Traditional Chinese (zh-TW) as primary language
- Taiwan-specific terminology and references
- Cultural sensitivity in medical communications

### Regulatory Compliance
- PDPA (Personal Data Protection Act) compliance
- MOHW (Ministry of Health and Welfare) guidelines
- Taiwan FDA medical device regulations awareness
- National Health Insurance (NHI) system integration

## Implementation Checklist

- [ ] No diagnostic language in any user-facing content
- [ ] Emergency numbers (119, 112) accessible within 2 clicks
- [ ] Medical disclaimers on all health-related responses
- [ ] Traditional Chinese language support (zh-TW)
- [ ] PDPA-compliant data handling
- [ ] Professional medical consultation guidance
- [ ] Taiwan health system references (MOHW, NHI)

## Validation Command

Run Taiwan medical compliance validation:
\`\`\`bash
node spec/tasks/medical/taiwan-medical-validation.js validate <task-file>
\`\`\`
`;
  }
}

// CLI usage
if (require.main === module) {
  const command = process.argv[2];
  const taskFile = process.argv[3];

  const validator = new TaiwanMedicalValidator();

  if (command === 'validate' && taskFile) {
    const fs = require('fs');

    if (!fs.existsSync(taskFile)) {
      console.error(`❌ Task file not found: ${taskFile}`);
      process.exit(1);
    }

    const content = fs.readFileSync(taskFile, 'utf-8');
    const results = validator.validateMedicalTask(content);

    console.log('\n🏥 Taiwan Medical Compliance Validation');
    console.log('='.repeat(50));
    console.log(`Overall Compliance: ${results.compliant ? '✅ PASS' : '❌ FAIL'}`);

    if (results.errors.length > 0) {
      console.log('\n❌ ERRORS:');
      results.errors.forEach((error, i) => console.log(`  ${i + 1}. ${error}`));
    }

    if (results.warnings.length > 0) {
      console.log('\n⚠️  WARNINGS:');
      results.warnings.forEach((warning, i) => console.log(`  ${i + 1}. ${warning}`));
    }

    if (results.recommendations.length > 0) {
      console.log('\n💡 RECOMMENDATIONS:');
      results.recommendations.forEach((rec, i) => console.log(`  ${i + 1}. ${rec}`));
    }

    console.log('\n🇹🇼 Taiwan-Specific Compliance:');
    Object.entries(results.taiwanSpecific).forEach(([key, value]) => {
      console.log(`  ${key}: ${value ? '✅' : '❌'}`);
    });

    process.exit(results.compliant ? 0 : 1);

  } else if (command === 'checklist') {
    const checklist = validator.generateComplianceChecklist();
    console.log('\n🏥 Taiwan Medical Compliance Checklist');
    console.log('='.repeat(50));

    Object.entries(checklist).forEach(([section, data]) => {
      console.log(`\n${data.title}:`);
      data.required.forEach(item => console.log(`  ✅ ${item}`));
      if (data.optional) {
        data.optional.forEach(item => console.log(`  🔄 ${item} (optional)`));
      }
    });

  } else if (command === 'template') {
    const featureName = taskFile || 'Medical Feature';
    const template = validator.generateTaiwanMedicalTaskTemplate(featureName);
    console.log(template);

  } else {
    console.log('Taiwan Medical Validation Tool');
    console.log('Usage:');
    console.log('  node taiwan-medical-validation.js validate <task-file>');
    console.log('  node taiwan-medical-validation.js checklist');
    console.log('  node taiwan-medical-validation.js template [feature-name]');
  }
}

module.exports = TaiwanMedicalValidator;