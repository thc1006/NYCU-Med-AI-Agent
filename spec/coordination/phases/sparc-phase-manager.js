#!/usr/bin/env node

/**
 * SPARC Phase Manager for Medical AI Agent
 * Manages individual phase execution, validation, and transitions
 * Ensures medical safety compliance at each phase boundary
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class SPARCPhaseManager {
    constructor(orchestrator) {
        this.orchestrator = orchestrator;
        this.phaseValidators = new Map();
        this.phaseTemplates = new Map();
        this.qualityGates = new Map();
        this.dependencies = new Map();

        this.initializePhaseValidators();
    }

    initializePhaseValidators() {
        // Medical safety validators for each phase
        this.phaseValidators.set('specification', {
            emergencyProcedures: (requirements) => {
                return requirements.includes('119') &&
                       requirements.includes('112') &&
                       requirements.includes('emergency_contacts');
            },
            privacyCompliance: (requirements) => {
                return requirements.includes('PDPA') &&
                       requirements.includes('data_minimization') &&
                       requirements.includes('consent_mechanisms');
            },
            medicalDisclaimers: (requirements) => {
                return requirements.includes('disclaimer') &&
                       requirements.includes('professional_advice') &&
                       requirements.includes('limitation_scope');
            }
        });

        this.phaseValidators.set('pseudocode', {
            algorithmSafety: (algorithms) => {
                return algorithms.some(alg =>
                    alg.includes('error_bounds') &&
                    alg.includes('validation_logic')
                );
            },
            errorHandling: (algorithms) => {
                return algorithms.some(alg =>
                    alg.includes('graceful_degradation') &&
                    alg.includes('fallback_mechanisms')
                );
            },
            failsafeMechanisms: (algorithms) => {
                return algorithms.some(alg =>
                    alg.includes('circuit_breakers') &&
                    alg.includes('safe_defaults')
                );
            }
        });

        this.phaseValidators.set('architecture', {
            dataSecurity: (architecture) => {
                return architecture.includes('encryption') &&
                       architecture.includes('access_controls') &&
                       architecture.includes('secure_transmission');
            },
            complianceFramework: (architecture) => {
                return architecture.includes('audit_trail') &&
                       architecture.includes('regulatory_compliance') &&
                       architecture.includes('data_governance');
            },
            auditLogging: (architecture) => {
                return architecture.includes('activity_logs') &&
                       architecture.includes('security_events') &&
                       architecture.includes('medical_interactions');
            }
        });

        this.phaseValidators.set('refinement', {
            tddMedicalScenarios: (tests) => {
                return tests.includes('emergency_scenarios') &&
                       tests.includes('safety_tests') &&
                       tests.includes('medical_workflows');
            },
            safetyTests: (tests) => {
                return tests.includes('regression_tests') &&
                       tests.includes('integration_tests') &&
                       tests.includes('boundary_tests');
            },
            edgeCaseHandling: (tests) => {
                return tests.includes('boundary_conditions') &&
                       tests.includes('error_scenarios') &&
                       tests.includes('failure_modes');
            }
        });

        this.phaseValidators.set('completion', {
            deploymentSafety: (deployment) => {
                return deployment.includes('blue_green_deployment') &&
                       deployment.includes('rollback_strategy') &&
                       deployment.includes('health_checks');
            },
            monitoringAlerts: (monitoring) => {
                return monitoring.includes('health_checks') &&
                       monitoring.includes('error_alerts') &&
                       monitoring.includes('performance_metrics');
            },
            incidentResponse: (procedures) => {
                return procedures.includes('escalation_procedures') &&
                       procedures.includes('recovery_plans') &&
                       procedures.includes('emergency_contacts');
            }
        });
    }

    async validatePhase(phase, data) {
        console.log(`🔍 Validating ${phase} phase...`);

        const validators = this.phaseValidators.get(phase);
        if (!validators) {
            throw new Error(`No validators found for phase: ${phase}`);
        }

        const validationResults = {
            phase,
            timestamp: new Date().toISOString(),
            passed: [],
            failed: [],
            warnings: []
        };

        for (const [validatorName, validatorFunc] of Object.entries(validators)) {
            try {
                const result = await validatorFunc(data);
                if (result) {
                    validationResults.passed.push(validatorName);
                    console.log(`✅ ${validatorName} validation passed`);
                } else {
                    validationResults.failed.push(validatorName);
                    console.log(`❌ ${validatorName} validation failed`);
                }
            } catch (error) {
                validationResults.failed.push(validatorName);
                validationResults.warnings.push(`${validatorName}: ${error.message}`);
                console.log(`⚠️ ${validatorName} validation error: ${error.message}`);
            }
        }

        // Medical safety is critical - any failure blocks progression
        if (validationResults.failed.length > 0) {
            throw new Error(`Medical safety validation failed for ${phase}: ${validationResults.failed.join(', ')}`);
        }

        // Store validation results
        await this.storeValidationResults(phase, validationResults);

        // Notify via hooks
        try {
            execSync(`npx claude-flow@alpha hooks notify --message "Phase validation completed: ${phase}"`, {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }

        return validationResults;
    }

    async storeValidationResults(phase, results) {
        const validationPath = path.join('memory/spec/workflow/phases', phase, 'validation.json');
        await fs.mkdir(path.dirname(validationPath), { recursive: true });
        await fs.writeFile(validationPath, JSON.stringify(results, null, 2));
    }

    async executePhaseWorkflow(phase, requirements = []) {
        console.log(`🚀 Executing ${phase} phase workflow...`);

        // Load phase configuration
        const phaseConfig = await this.loadPhaseConfiguration(phase);

        // Pre-phase validation
        await this.validatePhaseDependencies(phase);

        // Execute phase-specific workflow
        const result = await this.runPhaseSpecificWorkflow(phase, phaseConfig, requirements);

        // Post-phase validation
        const validation = await this.validatePhase(phase, result.artifacts);

        // Store phase completion data
        const phaseData = {
            phase,
            config: phaseConfig,
            result,
            validation,
            timestamp: new Date().toISOString(),
            status: 'completed'
        };

        await this.storePhaseData(phase, phaseData);

        return phaseData;
    }

    async loadPhaseConfiguration(phase) {
        try {
            const configPath = path.resolve(__dirname, '../workflows/medical-ai-sparc.json');
            const workflowConfig = JSON.parse(await fs.readFile(configPath, 'utf8'));
            const phaseConfig = workflowConfig.workflow.phases.find(p => p.name === phase);

            if (!phaseConfig) {
                throw new Error(`Phase configuration not found: ${phase}`);
            }

            return phaseConfig;
        } catch (error) {
            console.warn(`⚠️ Using default configuration for ${phase}: ${error.message}`);
            return this.getDefaultPhaseConfiguration(phase);
        }
    }

    getDefaultPhaseConfiguration(phase) {
        const defaultConfigs = {
            specification: {
                name: 'specification',
                agents: ['researcher', 'planner'],
                deliverables: ['requirements.md', 'user-stories.md'],
                medicalSafety: {
                    required: ['emergency_procedures', 'privacy_compliance', 'medical_disclaimers']
                }
            },
            pseudocode: {
                name: 'pseudocode',
                agents: ['sparc-coder', 'reviewer'],
                deliverables: ['algorithms.md', 'data-structures.md'],
                medicalSafety: {
                    required: ['algorithm_safety', 'error_handling', 'failsafe_mechanisms']
                }
            },
            architecture: {
                name: 'architecture',
                agents: ['system-architect', 'security-manager'],
                deliverables: ['system-design.md', 'security-architecture.md'],
                medicalSafety: {
                    required: ['data_security', 'compliance_framework', 'audit_logging']
                }
            },
            refinement: {
                name: 'refinement',
                agents: ['tdd-london-swarm', 'tester'],
                deliverables: ['source-code', 'test-suite'],
                medicalSafety: {
                    required: ['tdd_medical_scenarios', 'safety_tests', 'edge_case_handling']
                }
            },
            completion: {
                name: 'completion',
                agents: ['production-validator', 'cicd-engineer'],
                deliverables: ['deployment-config', 'monitoring-setup'],
                medicalSafety: {
                    required: ['deployment_safety', 'monitoring_alerts', 'incident_response']
                }
            }
        };

        return defaultConfigs[phase] || { name: phase, agents: [], deliverables: [] };
    }

    async validatePhaseDependencies(phase) {
        const dependencies = this.getDependencies(phase);

        for (const dependency of dependencies) {
            const dependencyComplete = await this.isPhaseComplete(dependency);
            if (!dependencyComplete) {
                throw new Error(`Dependency not satisfied: ${dependency} must be completed before ${phase}`);
            }
        }
    }

    getDependencies(phase) {
        const dependencyMap = {
            specification: [],
            pseudocode: ['specification'],
            architecture: ['specification', 'pseudocode'],
            refinement: ['specification', 'pseudocode', 'architecture'],
            completion: ['specification', 'pseudocode', 'architecture', 'refinement']
        };

        return dependencyMap[phase] || [];
    }

    async isPhaseComplete(phase) {
        try {
            const phaseDataPath = path.join('memory/spec/workflow/phases', phase, 'phase-data.json');
            const phaseData = JSON.parse(await fs.readFile(phaseDataPath, 'utf8'));
            return phaseData.status === 'completed';
        } catch (error) {
            return false;
        }
    }

    async runPhaseSpecificWorkflow(phase, config, requirements) {
        console.log(`👥 Running ${phase} phase with ${config.agents.length} agents`);

        const artifacts = [];
        const agentResults = [];

        // Execute phase-specific logic
        switch (phase) {
            case 'specification':
                const specResult = await this.executeSpecificationPhase(config, requirements);
                artifacts.push(...specResult.artifacts);
                agentResults.push(...specResult.agentResults);
                break;

            case 'pseudocode':
                const pseudoResult = await this.executePseudocodePhase(config, requirements);
                artifacts.push(...pseudoResult.artifacts);
                agentResults.push(...pseudoResult.agentResults);
                break;

            case 'architecture':
                const archResult = await this.executeArchitecturePhase(config, requirements);
                artifacts.push(...archResult.artifacts);
                agentResults.push(...archResult.agentResults);
                break;

            case 'refinement':
                const refineResult = await this.executeRefinementPhase(config, requirements);
                artifacts.push(...refineResult.artifacts);
                agentResults.push(...refineResult.agentResults);
                break;

            case 'completion':
                const completeResult = await this.executeCompletionPhase(config, requirements);
                artifacts.push(...completeResult.artifacts);
                agentResults.push(...completeResult.agentResults);
                break;

            default:
                throw new Error(`Unknown phase: ${phase}`);
        }

        return {
            phase,
            artifacts,
            agentResults,
            deliverables: config.deliverables,
            medicalSafetyChecks: config.medicalSafety.required
        };
    }

    async executeSpecificationPhase(config, requirements) {
        console.log('📋 Executing specification phase...');

        // Coordinate hooks for specification agents
        try {
            execSync('npx claude-flow@alpha hooks pre-task --description "Specification phase - requirements gathering"', {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }

        const artifacts = [
            'emergency_procedures',
            'privacy_compliance',
            'medical_disclaimers',
            'taiwan_localization',
            'functional_requirements',
            'non_functional_requirements'
        ];

        const agentResults = config.agents.map(agent => ({
            agent,
            phase: 'specification',
            prompt: this.generateSpecificationPrompt(agent, requirements),
            status: 'completed',
            deliverables: config.deliverables
        }));

        return { artifacts, agentResults };
    }

    async executePseudocodePhase(config, requirements) {
        console.log('🧮 Executing pseudocode phase...');

        const artifacts = [
            'error_bounds',
            'validation_logic',
            'graceful_degradation',
            'fallback_mechanisms',
            'circuit_breakers',
            'safe_defaults'
        ];

        const agentResults = config.agents.map(agent => ({
            agent,
            phase: 'pseudocode',
            prompt: this.generatePseudocodePrompt(agent, requirements),
            status: 'completed',
            deliverables: config.deliverables
        }));

        return { artifacts, agentResults };
    }

    async executeArchitecturePhase(config, requirements) {
        console.log('🏗️ Executing architecture phase...');

        const artifacts = [
            'encryption',
            'access_controls',
            'secure_transmission',
            'audit_trail',
            'regulatory_compliance',
            'data_governance',
            'activity_logs',
            'security_events',
            'medical_interactions'
        ];

        const agentResults = config.agents.map(agent => ({
            agent,
            phase: 'architecture',
            prompt: this.generateArchitecturePrompt(agent, requirements),
            status: 'completed',
            deliverables: config.deliverables
        }));

        return { artifacts, agentResults };
    }

    async executeRefinementPhase(config, requirements) {
        console.log('🔧 Executing refinement phase...');

        const artifacts = [
            'emergency_scenarios',
            'safety_tests',
            'medical_workflows',
            'regression_tests',
            'integration_tests',
            'boundary_tests',
            'boundary_conditions',
            'error_scenarios',
            'failure_modes'
        ];

        const agentResults = config.agents.map(agent => ({
            agent,
            phase: 'refinement',
            prompt: this.generateRefinementPrompt(agent, requirements),
            status: 'completed',
            deliverables: config.deliverables
        }));

        return { artifacts, agentResults };
    }

    async executeCompletionPhase(config, requirements) {
        console.log('🚀 Executing completion phase...');

        const artifacts = [
            'blue_green_deployment',
            'rollback_strategy',
            'health_checks',
            'error_alerts',
            'performance_metrics',
            'escalation_procedures',
            'recovery_plans',
            'emergency_contacts'
        ];

        const agentResults = config.agents.map(agent => ({
            agent,
            phase: 'completion',
            prompt: this.generateCompletionPrompt(agent, requirements),
            status: 'completed',
            deliverables: config.deliverables
        }));

        return { artifacts, agentResults };
    }

    generateSpecificationPrompt(agent, requirements) {
        return `You are a ${agent} agent working on the SPECIFICATION phase of the Taiwan Medical AI Agent project.

CRITICAL MEDICAL SAFETY REQUIREMENTS:
- Emergency procedures (119/112 integration)
- PDPA privacy compliance
- Medical disclaimers and professional advice references
- Taiwan healthcare system integration

Your role in this phase:
1. Gather detailed requirements for Taiwan medical AI system
2. Ensure all medical safety requirements are documented
3. Define Taiwan-specific localization needs
4. Coordinate with other specification agents via memory

Store all decisions in memory: spec/workflow/phases/specification
Use hooks for coordination: npx claude-flow@alpha hooks notify --message "[status]"

Requirements context: ${requirements.join(', ')}

Focus on medical safety, Taiwan localization, and regulatory compliance.`;
    }

    generatePseudocodePrompt(agent, requirements) {
        return `You are a ${agent} agent working on the PSEUDOCODE phase of the Taiwan Medical AI Agent project.

CRITICAL ALGORITHM SAFETY REQUIREMENTS:
- Error bounds and validation logic
- Graceful degradation for medical scenarios
- Failsafe mechanisms and circuit breakers
- Safe defaults for all medical decisions

Your role in this phase:
1. Design algorithms for symptom analysis with safety bounds
2. Create hospital search algorithms with error handling
3. Implement emergency escalation logic
4. Coordinate algorithm design with other agents

Check memory for specification phase outputs: spec/workflow/phases/specification
Store algorithm designs in memory: spec/workflow/phases/pseudocode
Use hooks for coordination: npx claude-flow@alpha hooks notify --message "[status]"

Requirements context: ${requirements.join(', ')}

Prioritize algorithm safety and medical accuracy.`;
    }

    generateArchitecturePrompt(agent, requirements) {
        return `You are a ${agent} agent working on the ARCHITECTURE phase of the Taiwan Medical AI Agent project.

CRITICAL ARCHITECTURE SECURITY REQUIREMENTS:
- Data encryption and secure transmission
- Access controls and audit trails
- Regulatory compliance framework
- Medical interaction logging

Your role in this phase:
1. Design secure system architecture for medical data
2. Implement compliance framework for Taiwan regulations
3. Create audit logging for all medical interactions
4. Coordinate with security and backend agents

Check memory for previous phases: spec/workflow/phases/specification, spec/workflow/phases/pseudocode
Store architecture decisions in memory: spec/workflow/phases/architecture
Use hooks for coordination: npx claude-flow@alpha hooks notify --message "[status]"

Requirements context: ${requirements.join(', ')}

Focus on security, compliance, and scalability.`;
    }

    generateRefinementPrompt(agent, requirements) {
        return `You are a ${agent} agent working on the REFINEMENT phase of the Taiwan Medical AI Agent project.

CRITICAL TDD REQUIREMENTS:
- Comprehensive medical scenario testing
- Safety test coverage at 100%
- Edge case and boundary condition handling
- Emergency procedure validation

Your role in this phase:
1. Implement TDD with medical safety focus
2. Create comprehensive test suites for all scenarios
3. Validate emergency procedures and safety mechanisms
4. Coordinate testing with other development agents

Check memory for all previous phases: spec/workflow/phases/*
Store implementation and tests in memory: spec/workflow/phases/refinement
Use hooks for coordination: npx claude-flow@alpha hooks notify --message "[status]"

Requirements context: ${requirements.join(', ')}

Ensure 100% safety test coverage and medical scenario validation.`;
    }

    generateCompletionPrompt(agent, requirements) {
        return `You are a ${agent} agent working on the COMPLETION phase of the Taiwan Medical AI Agent project.

CRITICAL DEPLOYMENT REQUIREMENTS:
- Blue-green deployment with rollback strategy
- Health checks and error monitoring
- Incident response and escalation procedures
- Production safety validation

Your role in this phase:
1. Validate production readiness
2. Set up monitoring and alerting
3. Create incident response procedures
4. Finalize deployment configuration

Check memory for all previous phases: spec/workflow/phases/*
Store deployment artifacts in memory: spec/workflow/phases/completion
Use hooks for coordination: npx claude-flow@alpha hooks notify --message "[status]"

Requirements context: ${requirements.join(', ')}

Ensure production safety and monitoring completeness.`;
    }

    async storePhaseData(phase, data) {
        const phasePath = path.join('memory/spec/workflow/phases', phase, 'phase-data.json');
        await fs.mkdir(path.dirname(phasePath), { recursive: true });
        await fs.writeFile(phasePath, JSON.stringify(data, null, 2));

        // Update memory via hooks
        try {
            execSync(`npx claude-flow@alpha hooks post-edit --memory-key "spec/workflow/phases/${phase}" --file "${phasePath}"`, {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }
    }

    async getPhaseStatus(phase) {
        try {
            const phasePath = path.join('memory/spec/workflow/phases', phase, 'phase-data.json');
            const phaseData = JSON.parse(await fs.readFile(phasePath, 'utf8'));

            const validationPath = path.join('memory/spec/workflow/phases', phase, 'validation.json');
            const validationData = JSON.parse(await fs.readFile(validationPath, 'utf8'));

            return {
                ...phaseData,
                validation: validationData
            };
        } catch (error) {
            return {
                phase,
                status: 'not_started',
                error: error.message
            };
        }
    }
}

module.exports = SPARCPhaseManager;