#!/usr/bin/env node

/**
 * Template Generator for Medical Features
 * Generates task breakdown templates for specific medical AI features
 */

const fs = require('fs');
const path = require('path');

class TemplateGenerator {
  constructor() {
    this.medicalFeatures = {
      'symptom-triage': {
        description: 'Symptom analysis and risk assessment system',
        requirements: ['REQ-01', 'REQ-02', 'REQ-03'],
        tasks: [
          {
            title: 'Create symptom input validation model',
            files: ['app/domain/symptom_models.py', 'tests/test_symptom_models.py'],
            success: 'Pydantic model validates symptom input and rejects inappropriate content',
            leverage: 'FastAPI request validation patterns'
          },
          {
            title: 'Implement emergency keyword detection',
            files: ['app/services/emergency_detection.py', 'tests/test_emergency.py'],
            success: 'System identifies high-risk symptoms and triggers emergency protocols',
            leverage: 'Pattern matching algorithms'
          },
          {
            title: 'Add medical disclaimer middleware',
            files: ['app/middlewares/disclaimer.py'],
            success: 'All medical responses include appropriate disclaimers and emergency contacts',
            leverage: 'FastAPI middleware framework'
          }
        ]
      },
      'hospital-search': {
        description: 'Location-based hospital and clinic search system',
        requirements: ['REQ-04', 'REQ-05', 'REQ-06'],
        tasks: [
          {
            title: 'Implement geolocation service',
            files: ['app/services/geolocation.py', 'tests/test_geolocation.py'],
            success: 'Service converts addresses to coordinates using Taiwan-specific geocoding',
            leverage: 'Google Geocoding API with zh-TW support'
          },
          {
            title: 'Create hospital search API integration',
            files: ['app/services/hospital_search.py', 'tests/test_hospital_search.py'],
            success: 'API returns nearby hospitals with Taiwan health system information',
            leverage: 'Google Places API with medical facility filters'
          },
          {
            title: 'Add MOHW hospital registry validation',
            files: ['app/services/mohw_registry.py', 'tests/test_registry.py'],
            success: 'System validates hospitals against official Taiwan health registry',
            leverage: 'MOHW open data APIs'
          }
        ]
      },
      'user-interface': {
        description: 'User interface for medical consultation and hospital search',
        requirements: ['REQ-07', 'REQ-08', 'REQ-09'],
        tasks: [
          {
            title: 'Create symptom input form with validation',
            files: ['frontend/components/SymptomForm.vue', 'frontend/tests/SymptomForm.test.js'],
            success: 'Form validates input and provides real-time safety guidance',
            leverage: 'Vue 3 composition API and form validation'
          },
          {
            title: 'Implement hospital results display',
            files: ['frontend/components/HospitalList.vue', 'frontend/tests/HospitalList.test.js'],
            success: 'Component displays hospital information with maps and contact details',
            leverage: 'Google Maps integration for Taiwan locations'
          },
          {
            title: 'Add emergency contact quick access',
            files: ['frontend/components/EmergencyContacts.vue'],
            success: 'Component provides one-click access to 119, 112, and other emergency services',
            leverage: 'Taiwan emergency services integration'
          }
        ]
      },
      'safety-compliance': {
        description: 'Medical safety and Taiwan regulatory compliance system',
        requirements: ['REQ-10', 'REQ-11', 'REQ-12'],
        tasks: [
          {
            title: 'Implement medical disclaimer system',
            files: ['app/services/compliance.py', 'tests/test_compliance.py'],
            success: 'System ensures all medical advice includes appropriate disclaimers',
            leverage: 'Taiwan medical regulation templates'
          },
          {
            title: 'Create audit logging for medical interactions',
            files: ['app/middlewares/audit.py', 'tests/test_audit.py'],
            success: 'System logs medical consultations while protecting patient privacy',
            leverage: 'PDPA-compliant logging framework'
          },
          {
            title: 'Add content filtering for diagnostic language',
            files: ['app/services/content_filter.py', 'tests/test_filter.py'],
            success: 'System prevents AI from providing medical diagnoses',
            leverage: 'NLP content classification models'
          }
        ]
      }
    };
  }

  /**
   * Generate task template for a specific feature
   */
  generateTemplate(featureName, outputPath = null) {
    if (!this.medicalFeatures[featureName]) {
      throw new Error(`Unknown medical feature: ${featureName}. Available: ${Object.keys(this.medicalFeatures).join(', ')}`);
    }

    const feature = this.medicalFeatures[featureName];
    const template = this.buildTemplate(featureName, feature);

    if (outputPath) {
      fs.writeFileSync(outputPath, template);
      console.log(`✅ Generated template for '${featureName}' at ${outputPath}`);
    }

    return template;
  }

  /**
   * Build the complete template content
   */
  buildTemplate(featureName, feature) {
    const timestamp = new Date().toISOString().split('T')[0];

    return `# ${this.titleCase(featureName)} - Task Breakdown

Generated: ${timestamp}

## Task Overview

${feature.description} for the Taiwan Medical AI Agent project.

## Steering Document Compliance

Reference to requirements and design documents:
- Requirements: spec/requirements.md (${feature.requirements.join(', ')})
- Design: spec/design.md
- Medical Safety: spec/medical-safety-guidelines.md

## Atomic Task Requirements

All tasks must meet these criteria:

### 1. **Medical Safety**
- ❌ No diagnostic language or medical advice
- ✅ Emergency contact integration (119, 112)
- ✅ Medical disclaimers on all responses
- ✅ Taiwan health regulation compliance

### 2. **Atomicity**
- ✅ 15-30 minute completion time
- ✅ 1-3 files maximum per task
- ✅ Single testable outcome
- ✅ Clear success criteria

### 3. **Taiwan Localization**
- ✅ Traditional Chinese (zh-TW) support
- ✅ Taiwan emergency services integration
- ✅ MOHW regulatory compliance
- ✅ Local medical system knowledge

## Tasks

${feature.tasks.map((task, index) => this.formatTask(task, index + 1)).join('\n\n')}

## Medical Safety Validation

Each task must be validated for:

- [ ] No diagnostic language in implementation
- [ ] Emergency contact accessibility
- [ ] Medical disclaimer compliance
- [ ] Taiwan health regulation adherence
- [ ] Patient privacy protection (PDPA)

## Testing Requirements

All tasks must include:

- [ ] Unit tests with medical safety validation
- [ ] Integration tests with Taiwan services
- [ ] E2E tests simulating real user scenarios
- [ ] Safety regression tests

## Dependencies

${this.generateDependencies(feature.tasks)}

## Completion Criteria

This feature is complete when:

- [ ] All tasks pass validation
- [ ] Medical safety tests pass
- [ ] Taiwan localization verified
- [ ] Emergency protocols tested
- [ ] Regulatory compliance confirmed

## Notes

- Medical content requires additional review by qualified personnel
- Taiwan emergency services (119, 112) must be prominently featured
- All medical responses must include disclaimers
- Patient data handling must comply with PDPA regulations
`;
  }

  /**
   * Format individual task
   */
  formatTask(task, number) {
    return `- [ ] ${number}. ${task.title}
  - **Files**: ${task.files.join(', ')}
  - **Success**: ${task.success}
  - **Leverage**: ${task.leverage}
  - **Medical Safety**: Ensure no diagnostic language and include emergency contacts`;
  }

  /**
   * Generate task dependencies section
   */
  generateDependencies(tasks) {
    return tasks.map((task, index) => {
      if (index === 0) {
        return `- Task ${index + 1}: No dependencies (can start immediately)`;
      }
      return `- Task ${index + 1}: Depends on Task ${index} completion`;
    }).join('\n');
  }

  /**
   * Convert kebab-case to Title Case
   */
  titleCase(str) {
    return str.split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  /**
   * List available features
   */
  listFeatures() {
    console.log('\n🏥 Available Medical Features:\n');
    Object.entries(this.medicalFeatures).forEach(([key, feature]) => {
      console.log(`  ${key.padEnd(20)} - ${feature.description}`);
    });
    console.log('\nUsage: node generate-template.js <feature-name> [output-file]');
  }
}

// CLI usage
if (require.main === module) {
  const featureName = process.argv[2];
  const outputFile = process.argv[3];

  const generator = new TemplateGenerator();

  if (!featureName) {
    generator.listFeatures();
    process.exit(0);
  }

  try {
    const template = generator.generateTemplate(featureName, outputFile);

    if (!outputFile) {
      console.log('\n' + '='.repeat(60));
      console.log('Generated Template:');
      console.log('='.repeat(60));
      console.log(template);
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
    process.exit(1);
  }
}

module.exports = TemplateGenerator;