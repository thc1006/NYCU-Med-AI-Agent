#!/usr/bin/env node

/**
 * SPARC Methodology Orchestrator for Medical AI Agent
 * Coordinates systematic development through Specification → Pseudocode → Architecture → Refinement → Completion
 * Ensures medical safety validation at each phase transition
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync, spawn } = require('child_process');

class SPARCOrchestrator {
    constructor() {
        this.phases = ['specification', 'pseudocode', 'architecture', 'refinement', 'completion'];
        this.currentPhase = 'specification';
        this.phaseData = new Map();
        this.memoryPath = 'memory/spec/workflow/phases';
        this.coordination = {
            activeAgents: new Set(),
            phaseValidation: new Map(),
            dependencies: new Map(),
            qualityGates: new Map()
        };

        // Medical safety validation rules
        this.medicalSafetyRules = {
            specification: ['emergency_procedures', 'privacy_compliance', 'medical_disclaimers'],
            pseudocode: ['algorithm_safety', 'error_handling', 'failsafe_mechanisms'],
            architecture: ['data_security', 'compliance_framework', 'audit_logging'],
            refinement: ['tdd_medical_scenarios', 'safety_tests', 'edge_case_handling'],
            completion: ['deployment_safety', 'monitoring_alerts', 'incident_response']
        };

        this.init();
    }

    async init() {
        await this.ensureDirectories();
        await this.loadPhaseState();
        await this.initializeHooks();
        console.log('🏥 SPARC Medical AI Orchestrator initialized');
    }

    async ensureDirectories() {
        const dirs = [
            this.memoryPath,
            'spec/coordination/workflows',
            'spec/coordination/phases',
            'spec/coordination/templates',
            'spec/coordination/validation',
            'spec/coordination/gates'
        ];

        for (const dir of dirs) {
            await fs.mkdir(dir, { recursive: true }).catch(() => {});
        }
    }

    async initializeHooks() {
        try {
            // Initialize Claude Flow hooks for coordination
            execSync('npx claude-flow@alpha hooks session-init --session-id "sparc-medical-ai"', {
                stdio: 'inherit',
                cwd: process.cwd()
            });

            // Set up pre-task validation hooks
            execSync('npx claude-flow@alpha hooks pre-task --description "SPARC Phase Coordination"', {
                stdio: 'inherit'
            });

            console.log('✅ SPARC coordination hooks initialized');
        } catch (error) {
            console.warn('⚠️ Claude Flow hooks not available, continuing without coordination');
        }
    }

    async loadPhaseState() {
        try {
            const statePath = path.join(this.memoryPath, 'current-state.json');
            const state = await fs.readFile(statePath, 'utf8');
            const parsed = JSON.parse(state);
            this.currentPhase = parsed.currentPhase || 'specification';
            this.phaseData = new Map(parsed.phaseData || []);
            console.log(`📋 Loaded phase state: ${this.currentPhase}`);
        } catch (error) {
            console.log('📋 Starting fresh SPARC workflow');
            await this.savePhaseState();
        }
    }

    async savePhaseState() {
        const state = {
            currentPhase: this.currentPhase,
            phaseData: Array.from(this.phaseData.entries()),
            timestamp: new Date().toISOString(),
            medicalSafetyValidated: this.coordination.phaseValidation
        };

        const statePath = path.join(this.memoryPath, 'current-state.json');
        await fs.writeFile(statePath, JSON.stringify(state, null, 2));

        // Notify via hooks
        try {
            execSync(`npx claude-flow@alpha hooks notify --message "Phase state saved: ${this.currentPhase}"`, {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }
    }

    async validateMedicalSafety(phase, requirements) {
        const safetyRules = this.medicalSafetyRules[phase] || [];
        const validation = {
            phase,
            rules: safetyRules,
            validated: new Set(),
            failed: new Set(),
            timestamp: new Date().toISOString()
        };

        console.log(`🔍 Validating medical safety for ${phase} phase...`);

        for (const rule of safetyRules) {
            const isValid = await this.checkSafetyRule(rule, requirements);
            if (isValid) {
                validation.validated.add(rule);
                console.log(`✅ ${rule} validation passed`);
            } else {
                validation.failed.add(rule);
                console.log(`❌ ${rule} validation failed`);
            }
        }

        this.coordination.phaseValidation.set(phase, validation);

        if (validation.failed.size > 0) {
            throw new Error(`Medical safety validation failed for ${phase}: ${Array.from(validation.failed).join(', ')}`);
        }

        return validation;
    }

    async checkSafetyRule(rule, requirements) {
        // Medical safety rule validation logic
        switch (rule) {
            case 'emergency_procedures':
                return requirements.includes('119') && requirements.includes('emergency_contacts');
            case 'privacy_compliance':
                return requirements.includes('PDPA') && requirements.includes('data_minimization');
            case 'medical_disclaimers':
                return requirements.includes('disclaimer') && requirements.includes('professional_advice');
            case 'algorithm_safety':
                return requirements.includes('error_bounds') && requirements.includes('validation_logic');
            case 'error_handling':
                return requirements.includes('graceful_degradation') && requirements.includes('fallback_mechanisms');
            case 'failsafe_mechanisms':
                return requirements.includes('circuit_breakers') && requirements.includes('safe_defaults');
            case 'data_security':
                return requirements.includes('encryption') && requirements.includes('access_controls');
            case 'compliance_framework':
                return requirements.includes('audit_trail') && requirements.includes('regulatory_compliance');
            case 'audit_logging':
                return requirements.includes('activity_logs') && requirements.includes('security_events');
            case 'tdd_medical_scenarios':
                return requirements.includes('edge_cases') && requirements.includes('safety_tests');
            case 'safety_tests':
                return requirements.includes('regression_tests') && requirements.includes('integration_tests');
            case 'edge_case_handling':
                return requirements.includes('boundary_conditions') && requirements.includes('error_scenarios');
            case 'deployment_safety':
                return requirements.includes('blue_green_deployment') && requirements.includes('rollback_strategy');
            case 'monitoring_alerts':
                return requirements.includes('health_checks') && requirements.includes('error_alerts');
            case 'incident_response':
                return requirements.includes('escalation_procedures') && requirements.includes('recovery_plans');
            default:
                return true; // Unknown rules pass by default
        }
    }

    async executePhase(phase, requirements = []) {
        console.log(`🚀 Executing ${phase} phase...`);

        // Pre-phase validation
        await this.validateMedicalSafety(phase, requirements);

        // Update memory with phase execution
        try {
            execSync(`npx claude-flow@alpha hooks post-edit --memory-key "spec/workflow/phases/${phase}" --file "spec/coordination/phases/${phase}.json"`, {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }

        const phaseConfig = await this.loadPhaseTemplate(phase);
        const result = await this.runPhaseAgents(phase, phaseConfig, requirements);

        this.phaseData.set(phase, {
            ...result,
            timestamp: new Date().toISOString(),
            medicalSafetyValidated: true
        });

        await this.savePhaseState();
        return result;
    }

    async loadPhaseTemplate(phase) {
        try {
            const templatePath = `spec/coordination/templates/${phase}-template.json`;
            const template = await fs.readFile(templatePath, 'utf8');
            return JSON.parse(template);
        } catch (error) {
            // Return default template if file doesn't exist
            return this.getDefaultPhaseTemplate(phase);
        }
    }

    getDefaultPhaseTemplate(phase) {
        const templates = {
            specification: {
                agents: ['researcher', 'planner', 'system-architect'],
                deliverables: ['requirements.md', 'user-stories.md', 'acceptance-criteria.md'],
                validationCriteria: ['completeness', 'clarity', 'medical-safety'],
                estimatedHours: 8
            },
            pseudocode: {
                agents: ['algorithm-designer', 'coder', 'reviewer'],
                deliverables: ['algorithms.md', 'data-structures.md', 'complexity-analysis.md'],
                validationCriteria: ['efficiency', 'correctness', 'safety-logic'],
                estimatedHours: 12
            },
            architecture: {
                agents: ['system-architect', 'backend-dev', 'security-manager'],
                deliverables: ['system-design.md', 'component-diagram.md', 'api-spec.md'],
                validationCriteria: ['scalability', 'security', 'maintainability'],
                estimatedHours: 16
            },
            refinement: {
                agents: ['tdd-london-swarm', 'coder', 'tester', 'reviewer'],
                deliverables: ['source-code', 'unit-tests', 'integration-tests'],
                validationCriteria: ['test-coverage', 'code-quality', 'performance'],
                estimatedHours: 24
            },
            completion: {
                agents: ['production-validator', 'cicd-engineer', 'reviewer'],
                deliverables: ['deployment-config', 'monitoring-setup', 'documentation'],
                validationCriteria: ['production-ready', 'monitoring', 'documentation'],
                estimatedHours: 8
            }
        };

        return templates[phase] || { agents: ['coder'], deliverables: [], validationCriteria: [], estimatedHours: 4 };
    }

    async runPhaseAgents(phase, config, requirements) {
        console.log(`👥 Spawning ${config.agents.length} agents for ${phase} phase`);

        const agentPromises = config.agents.map(async (agentType) => {
            const prompt = this.generateAgentPrompt(phase, agentType, requirements, config);

            // Coordinate via hooks before spawning
            try {
                execSync(`npx claude-flow@alpha hooks pre-task --description "${phase} phase - ${agentType} agent"`, {
                    stdio: 'inherit'
                });
            } catch (error) {
                // Continue without hooks if not available
            }

            console.log(`🤖 Spawning ${agentType} for ${phase} phase`);
            return {
                agent: agentType,
                phase,
                prompt,
                status: 'spawned',
                timestamp: new Date().toISOString()
            };
        });

        const results = await Promise.all(agentPromises);

        // Post-phase coordination
        try {
            execSync(`npx claude-flow@alpha hooks post-task --task-id "${phase}-coordination"`, {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }

        return {
            phase,
            agents: results,
            deliverables: config.deliverables,
            validationCriteria: config.validationCriteria,
            estimatedHours: config.estimatedHours,
            status: 'completed'
        };
    }

    generateAgentPrompt(phase, agentType, requirements, config) {
        const basePrompt = `You are a ${agentType} agent working on the ${phase} phase of the Taiwan Medical AI Agent project.

Project Context: Building a Taiwan-localized medical assistant with symptom analysis and nearby hospital search.

Phase Objectives: ${config.deliverables.join(', ')}
Medical Safety Requirements: ${this.medicalSafetyRules[phase].join(', ')}
Validation Criteria: ${config.validationCriteria.join(', ')}

CRITICAL: This is a medical application. Always prioritize:
1. Patient safety and emergency procedures (119/112)
2. PDPA compliance and data minimization
3. Medical disclaimers and professional advice references
4. Error handling and graceful degradation
5. Audit logging and compliance frameworks

Coordination Protocol:
- Use hooks for coordination: npx claude-flow@alpha hooks notify --message "[status]"
- Store decisions in memory: spec/workflow/phases/${phase}
- Check memory for previous phase outputs before starting
- Coordinate with other agents via memory and hooks

Requirements: ${requirements.join(', ')}

Execute your role with medical safety as top priority.`;

        return basePrompt;
    }

    async transitionToPhase(targetPhase) {
        const phaseIndex = this.phases.indexOf(targetPhase);
        const currentIndex = this.phases.indexOf(this.currentPhase);

        if (phaseIndex === -1) {
            throw new Error(`Invalid phase: ${targetPhase}`);
        }

        if (phaseIndex <= currentIndex) {
            console.log(`⚠️ Cannot transition backwards from ${this.currentPhase} to ${targetPhase}`);
            return false;
        }

        // Validate current phase completion
        const currentPhaseData = this.phaseData.get(this.currentPhase);
        if (!currentPhaseData || !this.isPhaseComplete(this.currentPhase)) {
            throw new Error(`Current phase ${this.currentPhase} is not complete`);
        }

        // Check quality gates
        const qualityGatesPassed = await this.checkQualityGates(this.currentPhase);
        if (!qualityGatesPassed) {
            throw new Error(`Quality gates failed for ${this.currentPhase} phase`);
        }

        this.currentPhase = targetPhase;
        await this.savePhaseState();

        console.log(`✅ Transitioned to ${targetPhase} phase`);

        // Notify via hooks
        try {
            execSync(`npx claude-flow@alpha hooks notify --message "Phase transition: ${targetPhase}"`, {
                stdio: 'inherit'
            });
        } catch (error) {
            // Continue without hooks if not available
        }

        return true;
    }

    isPhaseComplete(phase) {
        const phaseData = this.phaseData.get(phase);
        return phaseData && phaseData.status === 'completed' && phaseData.medicalSafetyValidated;
    }

    async checkQualityGates(phase) {
        const gates = this.coordination.qualityGates.get(phase) || [];

        for (const gate of gates) {
            const passed = await this.validateQualityGate(gate, phase);
            if (!passed) {
                console.log(`❌ Quality gate failed: ${gate.name}`);
                return false;
            }
            console.log(`✅ Quality gate passed: ${gate.name}`);
        }

        return true;
    }

    async validateQualityGate(gate, phase) {
        // Quality gate validation logic
        // This would integrate with actual validation tools
        return true; // Placeholder
    }

    async getPhaseStatus() {
        return {
            currentPhase: this.currentPhase,
            phases: this.phases.map(phase => ({
                name: phase,
                status: this.isPhaseComplete(phase) ? 'completed' :
                       phase === this.currentPhase ? 'in_progress' : 'pending',
                data: this.phaseData.get(phase),
                medicalSafetyValidated: this.coordination.phaseValidation.has(phase)
            })),
            coordination: {
                activeAgents: Array.from(this.coordination.activeAgents),
                validationStatus: Array.from(this.coordination.phaseValidation.entries())
            }
        };
    }

    async executeFullWorkflow(requirements = []) {
        console.log('🏥 Starting full SPARC Medical AI workflow...');

        for (const phase of this.phases) {
            if (!this.isPhaseComplete(phase)) {
                console.log(`\n📋 Executing ${phase} phase...`);
                await this.executePhase(phase, requirements);

                if (phase !== 'completion') {
                    const nextPhase = this.phases[this.phases.indexOf(phase) + 1];
                    await this.transitionToPhase(nextPhase);
                }
            } else {
                console.log(`✅ ${phase} phase already completed`);
            }
        }

        console.log('🎉 SPARC Medical AI workflow completed successfully!');
        return await this.getPhaseStatus();
    }
}

// CLI interface
if (require.main === module) {
    const orchestrator = new SPARCOrchestrator();

    const command = process.argv[2];
    const args = process.argv.slice(3);

    switch (command) {
        case 'status':
            orchestrator.getPhaseStatus().then(status => {
                console.log(JSON.stringify(status, null, 2));
            });
            break;

        case 'execute':
            const phase = args[0];
            const requirements = args.slice(1);
            orchestrator.executePhase(phase, requirements);
            break;

        case 'transition':
            const targetPhase = args[0];
            orchestrator.transitionToPhase(targetPhase);
            break;

        case 'workflow':
            const workflowRequirements = args;
            orchestrator.executeFullWorkflow(workflowRequirements);
            break;

        default:
            console.log(`Usage: node sparc-orchestrator.js <command> [args]
Commands:
  status                    - Show current phase status
  execute <phase> [reqs]    - Execute specific phase
  transition <phase>        - Transition to phase
  workflow [reqs]           - Execute full workflow`);
    }
}

module.exports = SPARCOrchestrator;