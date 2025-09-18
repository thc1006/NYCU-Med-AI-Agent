#!/usr/bin/env node

/**
 * SPARC CLI for Medical AI Agent Development
 * Command-line interface for managing SPARC methodology workflow
 * Integrates orchestration, phase management, and quality gates
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

// Import SPARC components
const SPARCOrchestrator = require('./sparc-orchestrator');
const SPARCPhaseManager = require('./phases/sparc-phase-manager');
const MedicalSafetyValidator = require('./validation/medical-safety-validator');
const QualityGates = require('./gates/quality-gates');

class SPARCCLI {
    constructor() {
        this.orchestrator = null;
        this.phaseManager = null;
        this.safetyValidator = null;
        this.qualityGates = null;
        this.initialized = false;
    }

    async initialize() {
        if (this.initialized) return;

        console.log('🏥 Initializing SPARC Medical AI Development Environment...');

        try {
            // Initialize SPARC components
            this.orchestrator = new SPARCOrchestrator();
            this.phaseManager = new SPARCPhaseManager(this.orchestrator);
            this.safetyValidator = new MedicalSafetyValidator();
            this.qualityGates = new QualityGates();

            // Initialize Claude Flow hooks
            await this.initializeClaudeFlowIntegration();

            this.initialized = true;
            console.log('✅ SPARC environment initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize SPARC environment:', error.message);
            throw error;
        }
    }

    async initializeClaudeFlowIntegration() {
        try {
            // Initialize swarm coordination
            execSync('npx claude-flow@alpha hooks session-init --session-id "sparc-medical-ai-coordination"', {
                stdio: 'inherit',
                cwd: process.cwd()
            });

            // Set up memory namespace
            execSync('npx claude-flow@alpha hooks post-edit --memory-key "spec/workflow/initialization" --file "spec/coordination/sparc-cli.js"', {
                stdio: 'inherit'
            });

            console.log('🔗 Claude Flow integration initialized');
        } catch (error) {
            console.warn('⚠️ Claude Flow hooks not available, continuing without coordination features');
        }
    }

    async runCommand(command, args) {
        await this.initialize();

        switch (command) {
            case 'init':
                return await this.initializeProject(args);
            case 'status':
                return await this.showStatus(args);
            case 'phase':
                return await this.managePhase(args);
            case 'validate':
                return await this.runValidation(args);
            case 'gates':
                return await this.runQualityGates(args);
            case 'workflow':
                return await this.runWorkflow(args);
            case 'safety':
                return await this.checkMedicalSafety(args);
            case 'emergency':
                return await this.validateEmergencyProcedures(args);
            case 'report':
                return await this.generateReport(args);
            case 'demo':
                return await this.runDemo(args);
            default:
                this.showHelp();
                return null;
        }
    }

    async initializeProject(args) {
        const projectName = args[0] || 'taiwan-medical-ai';
        console.log(`🚀 Initializing SPARC project: ${projectName}`);

        const projectConfig = {
            name: projectName,
            type: 'medical-ai',
            localization: 'taiwan',
            sparc_version: '1.0.0',
            medical_safety: {
                enabled: true,
                emergency_procedures: ['119', '112'],
                compliance_frameworks: ['pdpa', 'mohw']
            },
            phases: {
                current: 'specification',
                completed: [],
                blocked: []
            },
            initialized: new Date().toISOString()
        };

        // Create project configuration
        const configPath = path.join('memory/spec/workflow', 'project-config.json');
        await fs.mkdir(path.dirname(configPath), { recursive: true });
        await fs.writeFile(configPath, JSON.stringify(projectConfig, null, 2));

        // Initialize phase directories
        const phases = ['specification', 'pseudocode', 'architecture', 'refinement', 'completion'];
        for (const phase of phases) {
            const phaseDir = path.join('memory/spec/workflow/phases', phase);
            await fs.mkdir(phaseDir, { recursive: true });
        }

        // Create initial requirements template
        await this.createInitialRequirements();

        console.log(`✅ Project ${projectName} initialized with SPARC methodology`);
        console.log(`📋 Current phase: ${projectConfig.phases.current}`);
        console.log(`🛡️ Medical safety validation: enabled`);

        return projectConfig;
    }

    async createInitialRequirements() {
        const initialRequirements = [
            '119',
            '112',
            'emergency_contacts',
            'PDPA',
            'data_minimization',
            'disclaimer',
            'professional_advice',
            'taiwan_localization',
            'traditional_chinese'
        ];

        const requirementsPath = path.join('memory/spec/workflow', 'initial-requirements.json');
        await fs.writeFile(requirementsPath, JSON.stringify(initialRequirements, null, 2));
    }

    async showStatus(args) {
        const statusType = args[0] || 'overview';

        switch (statusType) {
            case 'overview':
                return await this.showOverviewStatus();
            case 'phases':
                return await this.showPhaseStatus();
            case 'safety':
                return await this.showSafetyStatus();
            case 'gates':
                return await this.showGateStatus();
            default:
                console.log('Unknown status type. Use: overview, phases, safety, gates');
                return null;
        }
    }

    async showOverviewStatus() {
        console.log('📊 SPARC Medical AI Development Status\n');

        try {
            // Get orchestrator status
            const orchestratorStatus = await this.orchestrator.getPhaseStatus();
            console.log(`Current Phase: ${orchestratorStatus.currentPhase}`);
            console.log(`Completed Phases: ${orchestratorStatus.phases.filter(p => p.status === 'completed').length}/5`);

            // Get safety status
            const safetyStatus = await this.safetyValidator.getMedicalSafetyStatus();
            console.log(`Overall Safety Score: ${safetyStatus.overall_safety_score}%`);
            console.log(`Critical Issues: ${safetyStatus.critical_issues.length}`);

            // Get quality gates status
            const gateStatus = await this.qualityGates.getAllGatesStatus();
            console.log(`Quality Gates Status: ${gateStatus.overall_status}`);
            console.log(`Passed Phases: ${gateStatus.passed_phases}/${gateStatus.total_phases}`);

            if (safetyStatus.critical_issues.length > 0) {
                console.log('\n🚨 CRITICAL SAFETY ISSUES:');
                for (const issue of safetyStatus.critical_issues) {
                    console.log(`  ❌ ${issue.phase}: ${issue.failures} failures`);
                }
            }

            return {
                orchestrator: orchestratorStatus,
                safety: safetyStatus,
                gates: gateStatus
            };
        } catch (error) {
            console.error('❌ Failed to get status:', error.message);
            return null;
        }
    }

    async showPhaseStatus() {
        console.log('📋 SPARC Phase Status\n');

        const phases = ['specification', 'pseudocode', 'architecture', 'refinement', 'completion'];
        for (const phase of phases) {
            try {
                const phaseStatus = await this.phaseManager.getPhaseStatus(phase);
                const statusIcon = phaseStatus.status === 'completed' ? '✅' :
                                 phaseStatus.status === 'in_progress' ? '🔄' : '⏳';
                console.log(`${statusIcon} ${phase}: ${phaseStatus.status}`);

                if (phaseStatus.validation) {
                    const validation = phaseStatus.validation;
                    console.log(`   Safety: ${validation.passed.length} passed, ${validation.failed.length} failed`);
                }
            } catch (error) {
                console.log(`❓ ${phase}: not started`);
            }
        }

        return null;
    }

    async showSafetyStatus() {
        console.log('🛡️ Medical Safety Status\n');

        try {
            const safetyStatus = await this.safetyValidator.getMedicalSafetyStatus();
            console.log(`Overall Safety Score: ${safetyStatus.overall_safety_score}%`);

            console.log('\nPhase Safety Scores:');
            for (const [phase, score] of Object.entries(safetyStatus.phase_scores)) {
                const scoreIcon = score >= 90 ? '🟢' : score >= 70 ? '🟡' : '🔴';
                console.log(`  ${scoreIcon} ${phase}: ${score}%`);
            }

            console.log('\nCompliance Status:');
            for (const [framework, statuses] of Object.entries(safetyStatus.compliance_status)) {
                const allCompliant = statuses.every(s => s.status === 'compliant');
                const statusIcon = allCompliant ? '✅' : '❌';
                console.log(`  ${statusIcon} ${framework}: ${allCompliant ? 'COMPLIANT' : 'NON-COMPLIANT'}`);
            }

            return safetyStatus;
        } catch (error) {
            console.error('❌ Failed to get safety status:', error.message);
            return null;
        }
    }

    async showGateStatus() {
        console.log('🚪 Quality Gates Status\n');

        try {
            const gateStatus = await this.qualityGates.getAllGatesStatus();
            console.log(`Overall Status: ${gateStatus.overall_status}`);
            console.log(`Passed Phases: ${gateStatus.passed_phases}/${gateStatus.total_phases}`);
            console.log(`Critical Failures: ${gateStatus.critical_failures}`);

            console.log('\nPhase Gate Details:');
            for (const [phase, details] of Object.entries(gateStatus.phase_details)) {
                if (details.overallStatus) {
                    const statusIcon = details.overallStatus === 'passed' ? '✅' :
                                     details.overallStatus === 'critical_failure' ? '🔴' : '🟡';
                    console.log(`  ${statusIcon} ${phase}: ${details.overallStatus} (${details.passedGates}/${details.totalGates})`);
                } else {
                    console.log(`  ❓ ${phase}: not validated`);
                }
            }

            return gateStatus;
        } catch (error) {
            console.error('❌ Failed to get gate status:', error.message);
            return null;
        }
    }

    async managePhase(args) {
        const action = args[0];
        const phase = args[1];

        switch (action) {
            case 'execute':
                return await this.executePhase(phase, args.slice(2));
            case 'transition':
                return await this.transitionPhase(phase);
            case 'validate':
                return await this.validatePhase(phase);
            case 'status':
                return await this.getPhaseDetails(phase);
            default:
                console.log('Phase actions: execute, transition, validate, status');
                return null;
        }
    }

    async executePhase(phase, requirements = []) {
        if (!phase) {
            console.error('❌ Phase name required');
            return null;
        }

        console.log(`🚀 Executing ${phase} phase...`);

        try {
            // Notify start via hooks
            execSync(`npx claude-flow@alpha hooks pre-task --description "Executing ${phase} phase"`, {
                stdio: 'inherit'
            });

            const result = await this.phaseManager.executePhaseWorkflow(phase, requirements);
            console.log(`✅ ${phase} phase completed successfully`);

            // Notify completion via hooks
            execSync(`npx claude-flow@alpha hooks post-task --task-id "${phase}-execution"`, {
                stdio: 'inherit'
            });

            return result;
        } catch (error) {
            console.error(`❌ Failed to execute ${phase} phase:`, error.message);
            return null;
        }
    }

    async transitionPhase(targetPhase) {
        if (!targetPhase) {
            console.error('❌ Target phase required');
            return null;
        }

        console.log(`🔄 Transitioning to ${targetPhase} phase...`);

        try {
            const success = await this.orchestrator.transitionToPhase(targetPhase);
            if (success) {
                console.log(`✅ Successfully transitioned to ${targetPhase} phase`);
            }
            return success;
        } catch (error) {
            console.error(`❌ Failed to transition to ${targetPhase}:`, error.message);
            return false;
        }
    }

    async validatePhase(phase) {
        if (!phase) {
            console.error('❌ Phase name required');
            return null;
        }

        console.log(`🔍 Validating ${phase} phase...`);

        try {
            // Get phase data
            const phaseData = await this.phaseManager.getPhaseStatus(phase);

            // Run medical safety validation
            const safetyResult = await this.safetyValidator.validateMedicalSafety(phase, phaseData.artifacts || [], phaseData.requirements || []);

            // Run quality gates
            const gateResult = await this.qualityGates.validatePhaseGates(phase, phaseData);

            console.log(`✅ ${phase} phase validation completed`);
            console.log(`   Safety Score: ${safetyResult.safety_score}%`);
            console.log(`   Quality Gates: ${gateResult.overallStatus} (${gateResult.passedGates}/${gateResult.totalGates})`);

            return {
                safety: safetyResult,
                gates: gateResult
            };
        } catch (error) {
            console.error(`❌ Failed to validate ${phase} phase:`, error.message);
            return null;
        }
    }

    async getPhaseDetails(phase) {
        if (!phase) {
            console.error('❌ Phase name required');
            return null;
        }

        try {
            const phaseStatus = await this.phaseManager.getPhaseStatus(phase);
            console.log(JSON.stringify(phaseStatus, null, 2));
            return phaseStatus;
        } catch (error) {
            console.error(`❌ Failed to get ${phase} phase details:`, error.message);
            return null;
        }
    }

    async runValidation(args) {
        const validationType = args[0] || 'all';

        switch (validationType) {
            case 'all':
                return await this.validateAllPhases();
            case 'safety':
                const phase = args[1];
                return await this.validateMedicalSafety(phase);
            case 'gates':
                const gatePhase = args[1];
                return await this.validateQualityGates(gatePhase);
            default:
                console.log('Validation types: all, safety, gates');
                return null;
        }
    }

    async validateAllPhases() {
        console.log('🔍 Running comprehensive validation for all phases...\n');

        const phases = ['specification', 'pseudocode', 'architecture', 'refinement', 'completion'];
        const results = {};

        for (const phase of phases) {
            try {
                console.log(`Validating ${phase} phase...`);
                const result = await this.validatePhase(phase);
                results[phase] = result;
            } catch (error) {
                console.log(`⚠️ ${phase} phase not ready for validation`);
                results[phase] = { error: error.message };
            }
        }

        return results;
    }

    async runWorkflow(args) {
        const workflowType = args[0] || 'full';

        switch (workflowType) {
            case 'full':
                return await this.runFullWorkflow(args.slice(1));
            case 'from':
                const startPhase = args[1];
                return await this.runWorkflowFromPhase(startPhase, args.slice(2));
            default:
                console.log('Workflow types: full, from <phase>');
                return null;
        }
    }

    async runFullWorkflow(requirements = []) {
        console.log('🚀 Starting full SPARC Medical AI workflow...\n');

        try {
            const result = await this.orchestrator.executeFullWorkflow(requirements);
            console.log('🎉 Full SPARC workflow completed successfully!');
            return result;
        } catch (error) {
            console.error('❌ Full workflow failed:', error.message);
            return null;
        }
    }

    async runWorkflowFromPhase(startPhase, requirements = []) {
        if (!startPhase) {
            console.error('❌ Start phase required');
            return null;
        }

        console.log(`🚀 Starting SPARC workflow from ${startPhase} phase...\n`);

        const phases = ['specification', 'pseudocode', 'architecture', 'refinement', 'completion'];
        const startIndex = phases.indexOf(startPhase);

        if (startIndex === -1) {
            console.error(`❌ Invalid phase: ${startPhase}`);
            return null;
        }

        try {
            for (let i = startIndex; i < phases.length; i++) {
                const phase = phases[i];
                console.log(`\n📋 Executing ${phase} phase...`);
                await this.executePhase(phase, requirements);

                if (i < phases.length - 1) {
                    const nextPhase = phases[i + 1];
                    await this.transitionPhase(nextPhase);
                }
            }

            console.log('🎉 Partial SPARC workflow completed successfully!');
            return true;
        } catch (error) {
            console.error('❌ Partial workflow failed:', error.message);
            return null;
        }
    }

    async checkMedicalSafety(args) {
        const action = args[0] || 'status';

        switch (action) {
            case 'status':
                return await this.showSafetyStatus();
            case 'validate':
                const phase = args[1];
                return await this.validateMedicalSafety(phase);
            case 'report':
                const reportPhase = args[1];
                return await this.generateSafetyReport(reportPhase);
            default:
                console.log('Safety actions: status, validate <phase>, report <phase>');
                return null;
        }
    }

    async validateMedicalSafety(phase) {
        if (!phase) {
            console.error('❌ Phase name required');
            return null;
        }

        try {
            const phaseData = await this.phaseManager.getPhaseStatus(phase);
            const result = await this.safetyValidator.validateMedicalSafety(phase, phaseData.artifacts || [], phaseData.requirements || []);
            console.log(`🛡️ Medical safety validation for ${phase}: ${result.overall_status}`);
            return result;
        } catch (error) {
            console.error(`❌ Medical safety validation failed for ${phase}:`, error.message);
            return null;
        }
    }

    async generateSafetyReport(phase) {
        if (!phase) {
            console.error('❌ Phase name required');
            return null;
        }

        try {
            const report = await this.safetyValidator.generateSafetyReport(phase);
            console.log(JSON.stringify(report, null, 2));
            return report;
        } catch (error) {
            console.error(`❌ Failed to generate safety report for ${phase}:`, error.message);
            return null;
        }
    }

    async validateEmergencyProcedures(args) {
        const data = args.length > 0 ? args : ['119', '112', 'emergency_contacts'];

        try {
            const result = await this.safetyValidator.validateEmergencyProcedures(data);
            console.log('🚨 Emergency Procedures Validation:');
            console.log(`Status: ${result.integration_status}`);
            console.log(`Validated: ${result.procedures_validated.length} procedures`);
            console.log(`Missing: ${result.missing_procedures.length} procedures`);

            if (result.missing_procedures.length > 0) {
                console.log('\nMissing Emergency Procedures:');
                for (const missing of result.missing_procedures) {
                    console.log(`  ❌ ${missing.code}: ${missing.description}`);
                }
            }

            return result;
        } catch (error) {
            console.error('❌ Emergency procedures validation failed:', error.message);
            return null;
        }
    }

    async generateReport(args) {
        const reportType = args[0] || 'overview';

        switch (reportType) {
            case 'overview':
                return await this.generateOverviewReport();
            case 'safety':
                const safetyPhase = args[1];
                return await this.generateSafetyReport(safetyPhase);
            case 'gates':
                const gatePhase = args[1];
                return await this.generateGateReport(gatePhase);
            default:
                console.log('Report types: overview, safety <phase>, gates <phase>');
                return null;
        }
    }

    async generateOverviewReport() {
        console.log('📊 Generating SPARC Medical AI Overview Report...\n');

        try {
            const status = await this.showOverviewStatus();
            const reportPath = path.join('memory/spec/workflow', 'overview-report.json');

            const report = {
                generated: new Date().toISOString(),
                type: 'overview',
                project: 'Taiwan Medical AI Agent',
                methodology: 'SPARC',
                status
            };

            await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
            console.log(`📄 Overview report generated: ${reportPath}`);

            return report;
        } catch (error) {
            console.error('❌ Failed to generate overview report:', error.message);
            return null;
        }
    }

    async runDemo(args) {
        const demoType = args[0] || 'basic';

        switch (demoType) {
            case 'basic':
                return await this.runBasicDemo();
            case 'safety':
                return await this.runSafetyDemo();
            case 'full':
                return await this.runFullDemo();
            default:
                console.log('Demo types: basic, safety, full');
                return null;
        }
    }

    async runBasicDemo() {
        console.log('🎯 Running Basic SPARC Demo...\n');

        try {
            // Initialize demo project
            await this.initializeProject(['demo-medical-ai']);

            // Show initial status
            console.log('\n📊 Initial Status:');
            await this.showStatus(['overview']);

            // Execute specification phase
            console.log('\n🚀 Executing Specification Phase:');
            await this.executePhase('specification', ['119', '112', 'PDPA', 'taiwan_localization']);

            // Validate specification
            console.log('\n🔍 Validating Specification:');
            await this.validatePhase('specification');

            // Show final status
            console.log('\n📊 Final Status:');
            await this.showStatus(['overview']);

            console.log('\n✅ Basic demo completed successfully!');
            return true;
        } catch (error) {
            console.error('❌ Basic demo failed:', error.message);
            return false;
        }
    }

    async runSafetyDemo() {
        console.log('🛡️ Running Medical Safety Demo...\n');

        try {
            // Test emergency procedures validation
            console.log('🚨 Testing Emergency Procedures:');
            await this.validateEmergencyProcedures(['119', '112', 'emergency_routing']);

            // Test medical safety validation
            console.log('\n🔍 Testing Medical Safety Validation:');
            await this.validateMedicalSafety('specification');

            // Show safety status
            console.log('\n📊 Safety Status:');
            await this.showSafetyStatus();

            console.log('\n✅ Safety demo completed successfully!');
            return true;
        } catch (error) {
            console.error('❌ Safety demo failed:', error.message);
            return false;
        }
    }

    async runFullDemo() {
        console.log('🎯 Running Full SPARC Demo...\n');

        try {
            // Run basic demo first
            await this.runBasicDemo();

            // Run safety demo
            await this.runSafetyDemo();

            // Execute additional phases
            console.log('\n🚀 Executing Additional Phases:');
            await this.executePhase('pseudocode', ['algorithm_safety', 'error_handling']);
            await this.executePhase('architecture', ['data_security', 'compliance_framework']);

            // Generate comprehensive report
            console.log('\n📄 Generating Comprehensive Report:');
            await this.generateOverviewReport();

            console.log('\n🎉 Full demo completed successfully!');
            return true;
        } catch (error) {
            console.error('❌ Full demo failed:', error.message);
            return false;
        }
    }

    showHelp() {
        console.log(`
🏥 SPARC Medical AI Development CLI

Usage: node sparc-cli.js <command> [options]

Commands:
  init [name]                    - Initialize SPARC project
  status [type]                  - Show status (overview|phases|safety|gates)
  phase <action> <phase> [args]  - Manage phases (execute|transition|validate|status)
  validate [type] [phase]        - Run validations (all|safety|gates)
  gates <phase>                  - Run quality gates for phase
  workflow <type> [args]         - Run workflows (full|from <phase>)
  safety <action> [phase]        - Medical safety operations (status|validate|report)
  emergency [data...]            - Validate emergency procedures
  report [type] [phase]          - Generate reports (overview|safety|gates)
  demo [type]                    - Run demos (basic|safety|full)

Examples:
  node sparc-cli.js init taiwan-medical-ai
  node sparc-cli.js status overview
  node sparc-cli.js phase execute specification 119 112 PDPA
  node sparc-cli.js validate all
  node sparc-cli.js workflow full
  node sparc-cli.js safety validate specification
  node sparc-cli.js demo basic

Taiwan Medical AI Agent SPARC Development
Medical Safety • Taiwan Compliance • Emergency Integration
        `);
    }
}

// CLI execution
if (require.main === module) {
    const cli = new SPARCCLI();
    const command = process.argv[2];
    const args = process.argv.slice(3);

    if (!command) {
        cli.showHelp();
        process.exit(0);
    }

    cli.runCommand(command, args)
        .then(result => {
            if (result !== null) {
                process.exit(0);
            } else {
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('❌ CLI Error:', error.message);
            process.exit(1);
        });
}

module.exports = SPARCCLI;