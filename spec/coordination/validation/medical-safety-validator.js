#!/usr/bin/env node

/**
 * Medical Safety Validator for Taiwan Medical AI Agent
 * Validates medical safety requirements across all SPARC phases
 * Ensures compliance with Taiwan medical regulations and safety standards
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class MedicalSafetyValidator {
    constructor() {
        this.validationRules = new Map();
        this.complianceFramework = new Map();
        this.emergencyProcedures = new Map();
        this.safetyMetrics = new Map();

        this.initializeValidationFramework();
    }

    initializeValidationFramework() {
        // Taiwan-specific medical safety rules
        this.validationRules.set('emergency_procedures', {
            required: ['119_integration', '112_integration', 'emergency_contacts', 'location_services'],
            validation: (data) => {
                return data.includes('119') &&
                       data.includes('112') &&
                       data.includes('emergency_routing') &&
                       data.includes('immediate_escalation');
            },
            severity: 'critical',
            description: 'Taiwan emergency services integration (119/112)'
        });

        this.validationRules.set('privacy_compliance', {
            required: ['pdpa_compliance', 'data_minimization', 'consent_mechanisms', 'retention_policies'],
            validation: (data) => {
                return data.includes('PDPA') &&
                       data.includes('minimal_collection') &&
                       data.includes('user_consent') &&
                       data.includes('data_encryption');
            },
            severity: 'critical',
            description: 'Taiwan Personal Data Protection Act compliance'
        });

        this.validationRules.set('medical_disclaimers', {
            required: ['disclaimer_text', 'professional_advice', 'limitation_scope', 'emergency_guidance'],
            validation: (data) => {
                return data.includes('medical_disclaimer') &&
                       data.includes('professional_consultation') &&
                       data.includes('emergency_services') &&
                       data.includes('service_limitations');
            },
            severity: 'critical',
            description: 'Medical disclaimers and professional advice guidance'
        });

        this.validationRules.set('algorithm_safety', {
            required: ['error_bounds', 'validation_logic', 'confidence_thresholds', 'uncertainty_handling'],
            validation: (data) => {
                return data.includes('error_boundaries') &&
                       data.includes('input_validation') &&
                       data.includes('confidence_scoring') &&
                       data.includes('uncertainty_flags');
            },
            severity: 'critical',
            description: 'Algorithm safety and validation mechanisms'
        });

        this.validationRules.set('error_handling', {
            required: ['graceful_degradation', 'fallback_mechanisms', 'error_recovery', 'safe_defaults'],
            validation: (data) => {
                return data.includes('graceful_failure') &&
                       data.includes('fallback_services') &&
                       data.includes('error_logging') &&
                       data.includes('default_safety');
            },
            severity: 'high',
            description: 'Error handling and graceful degradation'
        });

        this.validationRules.set('data_security', {
            required: ['encryption_at_rest', 'encryption_in_transit', 'access_controls', 'audit_logging'],
            validation: (data) => {
                return data.includes('encrypted_storage') &&
                       data.includes('secure_transmission') &&
                       data.includes('role_based_access') &&
                       data.includes('security_audit_trail');
            },
            severity: 'critical',
            description: 'Medical data security and protection'
        });

        // Taiwan compliance framework
        this.complianceFramework.set('pdpa', {
            name: 'Personal Data Protection Act',
            requirements: [
                'purpose_limitation',
                'data_minimization',
                'consent_mechanisms',
                'retention_policies',
                'cross_border_restrictions'
            ],
            authority: 'National Development Council',
            penalties: 'Up to NT$50 million or 5% of annual turnover'
        });

        this.complianceFramework.set('mohw', {
            name: 'Ministry of Health and Welfare Guidelines',
            requirements: [
                'medical_device_regulations',
                'healthcare_data_standards',
                'patient_safety_protocols',
                'medical_professional_oversight'
            ],
            authority: 'Ministry of Health and Welfare',
            penalties: 'License suspension or revocation'
        });

        // Emergency procedures for Taiwan
        this.emergencyProcedures.set('119', {
            service: 'Fire and EMS',
            description: 'Fire, ambulance, and emergency medical services',
            scope: 'Medical emergencies, accidents, disasters',
            response_time: '< 8 minutes urban, < 15 minutes rural'
        });

        this.emergencyProcedures.set('112', {
            service: 'International Emergency',
            description: 'GSM international emergency number',
            scope: 'Mobile phone emergency calls without SIM',
            response_time: 'Routes to appropriate service'
        });

        this.emergencyProcedures.set('110', {
            service: 'Police',
            description: 'Police and law enforcement',
            scope: 'Crime, traffic accidents, public safety',
            response_time: '< 5 minutes urban, < 10 minutes rural'
        });

        console.log('🛡️ Medical Safety Validator initialized with Taiwan compliance framework');
    }

    async validateMedicalSafety(phase, data, requirements = []) {
        console.log(`🔍 Validating medical safety for ${phase} phase...`);

        const validationResults = {
            phase,
            timestamp: new Date().toISOString(),
            overall_status: 'pending',
            critical_failures: [],
            high_failures: [],
            warnings: [],
            passed: [],
            compliance_status: new Map(),
            safety_score: 0
        };

        // Get phase-specific safety requirements
        const phaseRequirements = this.getPhaseRequirements(phase);

        for (const requirement of phaseRequirements) {
            const rule = this.validationRules.get(requirement);
            if (!rule) {
                validationResults.warnings.push(`Unknown safety requirement: ${requirement}`);
                continue;
            }

            try {
                const isValid = await this.validateSafetyRule(requirement, data, requirements);
                const result = {
                    rule: requirement,
                    severity: rule.severity,
                    description: rule.description,
                    status: isValid ? 'passed' : 'failed',
                    timestamp: new Date().toISOString()
                };

                if (isValid) {
                    validationResults.passed.push(result);
                    console.log(`✅ ${requirement} validation passed`);
                } else {
                    if (rule.severity === 'critical') {
                        validationResults.critical_failures.push(result);
                        console.log(`❌ CRITICAL: ${requirement} validation failed`);
                    } else if (rule.severity === 'high') {
                        validationResults.high_failures.push(result);
                        console.log(`⚠️ HIGH: ${requirement} validation failed`);
                    }
                }
            } catch (error) {
                validationResults.warnings.push(`Validation error for ${requirement}: ${error.message}`);
                console.log(`⚠️ Validation error for ${requirement}: ${error.message}`);
            }
        }

        // Validate Taiwan compliance
        await this.validateTaiwanCompliance(phase, data, validationResults);

        // Calculate safety score
        validationResults.safety_score = this.calculateSafetyScore(validationResults);

        // Determine overall status
        if (validationResults.critical_failures.length > 0) {
            validationResults.overall_status = 'critical_failure';
        } else if (validationResults.high_failures.length > 0) {
            validationResults.overall_status = 'high_risk';
        } else {
            validationResults.overall_status = 'passed';
        }

        // Store validation results
        await this.storeValidationResults(phase, validationResults);

        // Notify via hooks
        try {
            execSync(`npx claude-flow@alpha hooks notify --message "Medical safety validation: ${validationResults.overall_status}"`, {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }

        // Critical failures block progression
        if (validationResults.critical_failures.length > 0) {
            throw new Error(`Critical medical safety validation failures in ${phase}: ${validationResults.critical_failures.map(f => f.rule).join(', ')}`);
        }

        return validationResults;
    }

    getPhaseRequirements(phase) {
        const phaseRequirements = {
            specification: [
                'emergency_procedures',
                'privacy_compliance',
                'medical_disclaimers'
            ],
            pseudocode: [
                'algorithm_safety',
                'error_handling'
            ],
            architecture: [
                'data_security',
                'privacy_compliance'
            ],
            refinement: [
                'algorithm_safety',
                'error_handling',
                'emergency_procedures'
            ],
            completion: [
                'data_security',
                'emergency_procedures',
                'privacy_compliance'
            ]
        };

        return phaseRequirements[phase] || [];
    }

    async validateSafetyRule(rule, data, requirements) {
        const ruleConfig = this.validationRules.get(rule);
        if (!ruleConfig) {
            throw new Error(`Unknown safety rule: ${rule}`);
        }

        // Combine data sources for validation
        const combinedData = [
            ...(Array.isArray(data) ? data : [data]),
            ...requirements
        ].filter(item => typeof item === 'string');

        return ruleConfig.validation(combinedData);
    }

    async validateTaiwanCompliance(phase, data, validationResults) {
        console.log('🇹🇼 Validating Taiwan regulatory compliance...');

        for (const [framework, config] of this.complianceFramework.entries()) {
            const complianceResult = {
                framework,
                name: config.name,
                authority: config.authority,
                status: 'pending',
                requirements_met: [],
                requirements_failed: [],
                penalties: config.penalties
            };

            for (const requirement of config.requirements) {
                const isMet = await this.checkComplianceRequirement(requirement, data, phase);
                if (isMet) {
                    complianceResult.requirements_met.push(requirement);
                } else {
                    complianceResult.requirements_failed.push(requirement);
                }
            }

            complianceResult.status = complianceResult.requirements_failed.length === 0 ? 'compliant' : 'non_compliant';
            validationResults.compliance_status.set(framework, complianceResult);

            if (complianceResult.status === 'compliant') {
                console.log(`✅ ${config.name} compliance: PASSED`);
            } else {
                console.log(`❌ ${config.name} compliance: FAILED (${complianceResult.requirements_failed.join(', ')})`);
            }
        }
    }

    async checkComplianceRequirement(requirement, data, phase) {
        const combinedData = Array.isArray(data) ? data.join(' ') : data;

        switch (requirement) {
            case 'purpose_limitation':
                return combinedData.includes('purpose_defined') || combinedData.includes('data_purpose');
            case 'data_minimization':
                return combinedData.includes('minimal_collection') || combinedData.includes('data_minimization');
            case 'consent_mechanisms':
                return combinedData.includes('user_consent') || combinedData.includes('consent_flow');
            case 'retention_policies':
                return combinedData.includes('retention_policy') || combinedData.includes('data_retention');
            case 'cross_border_restrictions':
                return combinedData.includes('taiwan_only') || combinedData.includes('local_storage');
            case 'medical_device_regulations':
                return combinedData.includes('device_classification') || combinedData.includes('regulatory_approval');
            case 'healthcare_data_standards':
                return combinedData.includes('hl7_fhir') || combinedData.includes('medical_standards');
            case 'patient_safety_protocols':
                return combinedData.includes('safety_protocols') || combinedData.includes('patient_safety');
            case 'medical_professional_oversight':
                return combinedData.includes('medical_oversight') || combinedData.includes('professional_review');
            default:
                return false;
        }
    }

    calculateSafetyScore(validationResults) {
        const totalChecks = validationResults.passed.length +
                           validationResults.critical_failures.length +
                           validationResults.high_failures.length;

        if (totalChecks === 0) return 0;

        let score = (validationResults.passed.length / totalChecks) * 100;

        // Penalty for critical failures
        score -= validationResults.critical_failures.length * 20;

        // Penalty for high failures
        score -= validationResults.high_failures.length * 10;

        return Math.max(0, Math.round(score));
    }

    async storeValidationResults(phase, results) {
        const validationPath = path.join('memory/spec/workflow/phases', phase, 'medical-safety-validation.json');
        await fs.mkdir(path.dirname(validationPath), { recursive: true });

        // Convert Map to Object for JSON serialization
        const serializable = {
            ...results,
            compliance_status: Object.fromEntries(results.compliance_status)
        };

        await fs.writeFile(validationPath, JSON.stringify(serializable, null, 2));

        // Update memory via hooks
        try {
            execSync(`npx claude-flow@alpha hooks post-edit --memory-key "spec/medical-safety/${phase}" --file "${validationPath}"`, {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }
    }

    async generateSafetyReport(phase) {
        try {
            const validationPath = path.join('memory/spec/workflow/phases', phase, 'medical-safety-validation.json');
            const results = JSON.parse(await fs.readFile(validationPath, 'utf8'));

            const report = {
                phase,
                generation_time: new Date().toISOString(),
                overall_status: results.overall_status,
                safety_score: results.safety_score,
                summary: {
                    total_checks: results.passed.length + results.critical_failures.length + results.high_failures.length,
                    passed: results.passed.length,
                    critical_failures: results.critical_failures.length,
                    high_failures: results.high_failures.length,
                    warnings: results.warnings.length
                },
                compliance_summary: Object.values(results.compliance_status).map(comp => ({
                    framework: comp.framework,
                    name: comp.name,
                    status: comp.status,
                    requirements_met: comp.requirements_met.length,
                    requirements_failed: comp.requirements_failed.length
                })),
                recommendations: await this.generateRecommendations(results),
                emergency_procedures: Array.from(this.emergencyProcedures.entries()).map(([code, info]) => ({
                    code,
                    ...info
                }))
            };

            return report;
        } catch (error) {
            throw new Error(`Failed to generate safety report for ${phase}: ${error.message}`);
        }
    }

    async generateRecommendations(results) {
        const recommendations = [];

        // Critical failure recommendations
        for (const failure of results.critical_failures) {
            recommendations.push({
                priority: 'critical',
                rule: failure.rule,
                recommendation: this.getRecommendation(failure.rule),
                action_required: 'immediate'
            });
        }

        // High failure recommendations
        for (const failure of results.high_failures) {
            recommendations.push({
                priority: 'high',
                rule: failure.rule,
                recommendation: this.getRecommendation(failure.rule),
                action_required: 'before_next_phase'
            });
        }

        // Compliance recommendations
        for (const [framework, compliance] of Object.entries(results.compliance_status)) {
            if (compliance.status === 'non_compliant') {
                recommendations.push({
                    priority: 'critical',
                    framework: compliance.name,
                    recommendation: `Address failed requirements: ${compliance.requirements_failed.join(', ')}`,
                    action_required: 'immediate',
                    penalties: compliance.penalties
                });
            }
        }

        return recommendations;
    }

    getRecommendation(rule) {
        const recommendations = {
            emergency_procedures: 'Implement 119/112 emergency service integration with immediate escalation for critical symptoms',
            privacy_compliance: 'Ensure PDPA compliance with data minimization, user consent, and secure data handling',
            medical_disclaimers: 'Add prominent medical disclaimers and professional consultation recommendations',
            algorithm_safety: 'Implement error bounds, validation logic, and confidence thresholds for all algorithms',
            error_handling: 'Add graceful degradation, fallback mechanisms, and safe defaults for error scenarios',
            data_security: 'Implement encryption at rest and in transit, access controls, and audit logging'
        };

        return recommendations[rule] || 'Review and address the failed safety requirement';
    }

    async validateEmergencyProcedures(data) {
        console.log('🚨 Validating emergency procedures...');

        const emergencyValidation = {
            timestamp: new Date().toISOString(),
            procedures_validated: [],
            missing_procedures: [],
            integration_status: 'pending'
        };

        for (const [code, info] of this.emergencyProcedures.entries()) {
            const isImplemented = data.includes(code) || data.includes(info.service.toLowerCase());
            if (isImplemented) {
                emergencyValidation.procedures_validated.push({ code, ...info });
            } else {
                emergencyValidation.missing_procedures.push({ code, ...info });
            }
        }

        emergencyValidation.integration_status = emergencyValidation.missing_procedures.length === 0 ? 'complete' : 'incomplete';

        return emergencyValidation;
    }

    async getMedicalSafetyStatus() {
        const phases = ['specification', 'pseudocode', 'architecture', 'refinement', 'completion'];
        const status = {
            overall_safety_score: 0,
            phase_scores: {},
            critical_issues: [],
            compliance_status: {},
            last_updated: new Date().toISOString()
        };

        let totalScore = 0;
        let validatedPhases = 0;

        for (const phase of phases) {
            try {
                const report = await this.generateSafetyReport(phase);
                status.phase_scores[phase] = report.safety_score;
                totalScore += report.safety_score;
                validatedPhases++;

                // Collect critical issues
                if (report.summary.critical_failures > 0) {
                    status.critical_issues.push({
                        phase,
                        failures: report.summary.critical_failures
                    });
                }

                // Collect compliance status
                for (const comp of report.compliance_summary) {
                    if (!status.compliance_status[comp.framework]) {
                        status.compliance_status[comp.framework] = [];
                    }
                    status.compliance_status[comp.framework].push({
                        phase,
                        status: comp.status
                    });
                }
            } catch (error) {
                console.log(`⚠️ No safety validation data for ${phase} phase`);
            }
        }

        status.overall_safety_score = validatedPhases > 0 ? Math.round(totalScore / validatedPhases) : 0;

        return status;
    }
}

// CLI interface
if (require.main === module) {
    const validator = new MedicalSafetyValidator();

    const command = process.argv[2];
    const args = process.argv.slice(3);

    switch (command) {
        case 'validate':
            const phase = args[0];
            const data = args.slice(1);
            validator.validateMedicalSafety(phase, data);
            break;

        case 'report':
            const reportPhase = args[0];
            validator.generateSafetyReport(reportPhase).then(report => {
                console.log(JSON.stringify(report, null, 2));
            });
            break;

        case 'status':
            validator.getMedicalSafetyStatus().then(status => {
                console.log(JSON.stringify(status, null, 2));
            });
            break;

        case 'emergency':
            const emergencyData = args;
            validator.validateEmergencyProcedures(emergencyData).then(result => {
                console.log(JSON.stringify(result, null, 2));
            });
            break;

        default:
            console.log(`Usage: node medical-safety-validator.js <command> [args]
Commands:
  validate <phase> [data]   - Validate medical safety for phase
  report <phase>            - Generate safety report for phase
  status                    - Get overall medical safety status
  emergency [data]          - Validate emergency procedures`);
    }
}

module.exports = MedicalSafetyValidator;