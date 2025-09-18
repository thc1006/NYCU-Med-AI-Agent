#!/usr/bin/env node

/**
 * Proactive Validation Orchestrator
 *
 * Coordinates all validation systems for comprehensive design document validation
 * Automatically triggers validation and stores results in memory for team access
 * Integrates with Claude-Flow hooks for real-time validation feedback
 */

const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');

// Import individual validators
const SpecDesignValidator = require('./spec-design-validator');
const TaiwanLocalizationValidator = require('./taiwan-localization-validator');
const PDPAPrivacyValidator = require('./pdpa-privacy-validator');
const TDDReadinessValidator = require('./tdd-readiness-validator');

class ProactiveValidationOrchestrator {
    constructor() {
        this.validators = {
            design: new SpecDesignValidator(),
            taiwan: new TaiwanLocalizationValidator(),
            pdpa: new PDPAPrivacyValidator(),
            tdd: new TDDReadinessValidator()
        };

        this.validationResults = new Map();
        this.validationHistory = [];
        this.hooks = {
            enabled: true,
            triggerDelay: 3000, // 3 seconds after file change
            batchValidation: true
        };
    }

    async initialize() {
        console.log('🔄 Initializing Proactive Validation Orchestrator...');

        try {
            // Initialize Claude-Flow hooks
            await this.initializeHooks();

            // Setup file watchers
            await this.setupFileWatchers();

            // Initialize memory storage
            await this.initializeMemoryStore();

            console.log('✅ Proactive validation orchestrator active');
            console.log('📋 Available validators: design, taiwan, pdpa, tdd');
            console.log('👀 Watching .claude/specs/ for design document changes');

            return true;
        } catch (error) {
            console.error('❌ Failed to initialize validation orchestrator:', error);
            return false;
        }
    }

    async validateDesignDocument(designPath, options = {}) {
        const {
            validators = ['design', 'taiwan', 'pdpa', 'tdd'],
            requirementsPath = null,
            templatePath = null,
            storeResults = true,
            notifyTeam = true
        } = options;

        console.log(`\n🔍 Starting comprehensive validation for: ${path.basename(designPath)}`);
        console.log(`📊 Running validators: ${validators.join(', ')}`);

        const validationSession = {
            timestamp: new Date().toISOString(),
            designPath,
            validators: validators.slice(),
            results: {},
            summary: {
                overall: 'PENDING',
                passCount: 0,
                issueCount: 0,
                strengthCount: 0
            }
        };

        try {
            // Run all requested validators in parallel
            const validationPromises = validators.map(async (validatorName) => {
                console.log(`  🧪 Running ${validatorName} validator...`);

                const startTime = Date.now();
                let result;

                switch (validatorName) {
                    case 'design':
                        result = await this.validators.design.validateDesign(
                            designPath, requirementsPath, templatePath
                        );
                        break;
                    case 'taiwan':
                        result = await this.validators.taiwan.validateDocument(designPath);
                        break;
                    case 'pdpa':
                        result = await this.validators.pdpa.validateDocument(designPath);
                        break;
                    case 'tdd':
                        result = await this.validators.tdd.validateDocument(designPath);
                        break;
                    default:
                        throw new Error(`Unknown validator: ${validatorName}`);
                }

                const duration = Date.now() - startTime;
                console.log(`  ✅ ${validatorName} validation completed (${duration}ms)`);

                return { validatorName, result, duration };
            });

            // Wait for all validations to complete
            const validationResults = await Promise.all(validationPromises);

            // Process results
            for (const { validatorName, result, duration } of validationResults) {
                validationSession.results[validatorName] = {
                    ...result,
                    duration,
                    timestamp: new Date().toISOString()
                };

                // Update summary
                if (this.isPassingResult(result)) {
                    validationSession.summary.passCount++;
                } else {
                    validationSession.summary.issueCount += this.countIssues(result);
                }

                validationSession.summary.strengthCount += this.countStrengths(result);
            }

            // Calculate overall result
            validationSession.summary.overall = this.calculateOverallRating(validationSession);

            // Store results if requested
            if (storeResults) {
                await this.storeValidationSession(validationSession);
            }

            // Notify team if requested
            if (notifyTeam) {
                await this.notifyValidationComplete(validationSession);
            }

            // Print comprehensive report
            this.printValidationSummary(validationSession);

            return validationSession;

        } catch (error) {
            console.error(`❌ Validation failed for ${designPath}:`, error.message);
            validationSession.summary.overall = 'ERROR';
            validationSession.error = error.message;
            return validationSession;
        }
    }

    isPassingResult(result) {
        const rating = result.overall || result.rating || 'UNKNOWN';
        return rating.includes('PASS') ||
               rating.includes('EXCELLENT') ||
               rating.includes('COMPLIANT') ||
               rating.includes('READY');
    }

    countIssues(result) {
        if (result.breakdown) {
            return Object.keys(result.breakdown)
                .filter(key => key !== 'strengths')
                .reduce((sum, key) => sum + (result.breakdown[key]?.length || 0), 0);
        }
        if (result.details) {
            return Object.keys(result.details)
                .filter(key => key !== 'strengths')
                .reduce((sum, key) => sum + (result.details[key]?.length || 0), 0);
        }
        return 0;
    }

    countStrengths(result) {
        if (result.breakdown?.strengths) {
            return result.breakdown.strengths.length;
        }
        if (result.details?.strengths) {
            return result.details.strengths.length;
        }
        return 0;
    }

    calculateOverallRating(session) {
        const totalValidators = Object.keys(session.results).length;
        const passCount = session.summary.passCount;
        const issueCount = session.summary.issueCount;

        if (passCount === totalValidators && issueCount === 0) {
            return 'COMPREHENSIVE_PASS';
        } else if (passCount >= totalValidators * 0.75 && issueCount <= 5) {
            return 'MOSTLY_COMPLIANT';
        } else if (passCount >= totalValidators * 0.5) {
            return 'NEEDS_IMPROVEMENT';
        } else {
            return 'MAJOR_ISSUES';
        }
    }

    async storeValidationSession(session) {
        const featureName = path.basename(path.dirname(session.designPath));
        const memoryKey = `spec/validation/${featureName}/comprehensive/${Date.now()}`;

        try {
            // Store in local memory
            this.validationResults.set(memoryKey, session);
            this.validationHistory.push(session);

            // Store via Claude-Flow hooks
            await this.executeCommand('npx', [
                'claude-flow@alpha',
                'hooks',
                'memory-store',
                '--key', memoryKey,
                '--data', JSON.stringify(session)
            ]);

            // Write to local file cache
            const reportDir = path.join(
                path.dirname(session.designPath),
                '..',
                'validation',
                'reports'
            );

            await fs.mkdir(reportDir, { recursive: true });

            const reportPath = path.join(
                reportDir,
                `${featureName}-comprehensive-${Date.now()}.json`
            );

            await fs.writeFile(reportPath, JSON.stringify(session, null, 2));

            console.log(`💾 Validation session stored:`);
            console.log(`  Memory key: ${memoryKey}`);
            console.log(`  Report file: ${reportPath}`);

        } catch (error) {
            console.warn('⚠️ Could not store validation session:', error.message);
        }
    }

    async notifyValidationComplete(session) {
        const featureName = path.basename(path.dirname(session.designPath));
        const message = `Comprehensive validation completed for ${featureName}: ${session.summary.overall}`;

        try {
            await this.executeCommand('npx', [
                'claude-flow@alpha',
                'hooks',
                'notify',
                '--message', message,
                '--type', 'comprehensive-validation-complete',
                '--data', JSON.stringify({
                    designPath: session.designPath,
                    overall: session.summary.overall,
                    validators: session.validators,
                    passCount: session.summary.passCount,
                    issueCount: session.summary.issueCount
                })
            ]);

            console.log(`📢 Team notification sent: ${message}`);

        } catch (error) {
            console.warn('⚠️ Could not send team notification:', error.message);
        }
    }

    printValidationSummary(session) {
        console.log('\n🎯 COMPREHENSIVE VALIDATION SUMMARY');
        console.log('='.repeat(60));
        console.log(`Design: ${path.basename(session.designPath)}`);
        console.log(`Overall Rating: ${session.summary.overall}`);
        console.log(`Validators: ${session.validators.join(', ')}`);
        console.log(`Pass Rate: ${session.summary.passCount}/${session.validators.length}`);
        console.log(`Total Issues: ${session.summary.issueCount}`);
        console.log(`Total Strengths: ${session.summary.strengthCount}`);
        console.log('');

        // Show individual validator results
        console.log('📊 Individual Validator Results:');
        Object.entries(session.results).forEach(([validator, result]) => {
            const rating = result.overall || result.rating || 'UNKNOWN';
            const status = this.isPassingResult(result) ? '✅' : '❌';
            const duration = result.duration || 0;
            console.log(`  ${status} ${validator.toUpperCase()}: ${rating} (${duration}ms)`);
        });

        // Show critical issues that need attention
        console.log('');
        console.log('⚠️  Critical Issues Requiring Attention:');
        const criticalIssues = this.extractCriticalIssues(session);
        if (criticalIssues.length === 0) {
            console.log('  ✅ No critical issues found');
        } else {
            criticalIssues.forEach(issue => {
                console.log(`  🚨 ${issue.validator}: ${issue.issue}`);
            });
        }

        // Show overall recommendations
        console.log('');
        console.log('📋 Next Steps:');
        const recommendations = this.generateOverallRecommendations(session);
        recommendations.forEach(rec => {
            console.log(`  ${rec.priority === 'Critical' ? '🔴' : rec.priority === 'High' ? '🟡' : '🟢'} ${rec.action}`);
        });

        console.log('='.repeat(60));
    }

    extractCriticalIssues(session) {
        const criticalIssues = [];

        Object.entries(session.results).forEach(([validator, result]) => {
            // Extract critical issues from each validator
            if (result.breakdown) {
                Object.entries(result.breakdown).forEach(([category, issues]) => {
                    if (Array.isArray(issues) && category !== 'strengths') {
                        issues.forEach(issue => {
                            if (this.isCriticalIssue(issue, validator)) {
                                criticalIssues.push({ validator, category, issue });
                            }
                        });
                    }
                });
            }
        });

        return criticalIssues;
    }

    isCriticalIssue(issue, validator) {
        const criticalKeywords = [
            'missing.*emergency',
            'no.*disclaimer',
            'no.*consent',
            'major.*issues',
            'critical.*problem',
            'security.*vulnerability',
            'privacy.*violation',
            'medical.*safety'
        ];

        const issueText = issue.toLowerCase();
        return criticalKeywords.some(keyword => {
            const regex = new RegExp(keyword);
            return regex.test(issueText);
        });
    }

    generateOverallRecommendations(session) {
        const recommendations = [];

        if (session.summary.overall === 'MAJOR_ISSUES') {
            recommendations.push({
                priority: 'Critical',
                action: 'Address major validation issues before proceeding with implementation'
            });
        }

        if (session.summary.issueCount > 10) {
            recommendations.push({
                priority: 'High',
                action: 'Review and prioritize the numerous validation issues found'
            });
        }

        // Taiwan localization recommendations
        if (session.results.taiwan && !this.isPassingResult(session.results.taiwan)) {
            recommendations.push({
                priority: 'High',
                action: 'Complete Taiwan localization requirements (zh-TW, emergency numbers, healthcare integration)'
            });
        }

        // PDPA compliance recommendations
        if (session.results.pdpa && !this.isPassingResult(session.results.pdpa)) {
            recommendations.push({
                priority: 'Critical',
                action: 'Address PDPA privacy compliance issues before handling any user data'
            });
        }

        // TDD readiness recommendations
        if (session.results.tdd && !this.isPassingResult(session.results.tdd)) {
            recommendations.push({
                priority: 'Medium',
                action: 'Prepare TDD infrastructure and testing strategy before implementation'
            });
        }

        if (recommendations.length === 0) {
            recommendations.push({
                priority: 'Low',
                action: 'Design validation successful - proceed with implementation following TDD methodology'
            });
        }

        return recommendations;
    }

    async initializeHooks() {
        if (!this.hooks.enabled) return;

        const hookTypes = ['pre-edit', 'post-edit', 'session-restore', 'session-end'];

        for (const hookType of hookTypes) {
            try {
                await this.executeCommand('npx', [
                    'claude-flow@alpha',
                    'hooks',
                    'register',
                    hookType,
                    '--handler',
                    __filename
                ]);
                console.log(`📋 Registered ${hookType} hook`);
            } catch (error) {
                console.warn(`⚠️ Could not register ${hookType} hook:`, error.message);
            }
        }
    }

    async setupFileWatchers() {
        const specsPath = path.join(process.cwd(), '.claude', 'specs');

        try {
            await fs.access(specsPath);
            console.log(`👀 Watching design documents in: ${specsPath}`);

            // Simple polling-based file watcher
            setInterval(() => {
                this.checkForDesignChanges(specsPath);
            }, 5000); // Check every 5 seconds

        } catch (error) {
            console.warn('⚠️ Specs directory not found, creating...');
            await fs.mkdir(specsPath, { recursive: true });
        }
    }

    async checkForDesignChanges(specsPath) {
        try {
            const entries = await fs.readdir(specsPath, { withFileTypes: true });

            for (const entry of entries) {
                if (entry.isDirectory()) {
                    const featurePath = path.join(specsPath, entry.name);
                    const designPath = path.join(featurePath, 'design.md');

                    try {
                        const stats = await fs.stat(designPath);
                        const lastModified = stats.mtime.getTime();
                        const cacheKey = `lastModified:${designPath}`;

                        // Check if we've seen this file before
                        const cachedTime = this.getCachedModificationTime(cacheKey);

                        if (lastModified > cachedTime) {
                            this.setCachedModificationTime(cacheKey, lastModified);

                            // Trigger validation after a delay to allow file writing to complete
                            setTimeout(() => {
                                this.triggerComprehensiveValidation(designPath, 'file-change');
                            }, this.hooks.triggerDelay);
                        }
                    } catch (error) {
                        // design.md doesn't exist yet
                    }
                }
            }
        } catch (error) {
            console.warn('⚠️ Error checking for design changes:', error.message);
        }
    }

    async triggerComprehensiveValidation(designPath, trigger) {
        console.log(`\n🔍 Auto-triggering comprehensive validation for: ${path.basename(designPath)} (${trigger})`);

        // Find related files
        const featureDir = path.dirname(designPath);
        const requirementsPath = path.join(featureDir, 'requirements.md');
        const templatePath = path.join(process.cwd(), '.claude', 'templates', 'design-template.md');

        // Check if requirements.md exists
        let reqPath = null;
        try {
            await fs.access(requirementsPath);
            reqPath = requirementsPath;
        } catch (error) {
            // requirements.md doesn't exist
        }

        // Check if template exists
        let tempPath = null;
        try {
            await fs.access(templatePath);
            tempPath = templatePath;
        } catch (error) {
            // template doesn't exist
        }

        // Run comprehensive validation
        await this.validateDesignDocument(designPath, {
            validators: ['design', 'taiwan', 'pdpa', 'tdd'],
            requirementsPath: reqPath,
            templatePath: tempPath,
            storeResults: true,
            notifyTeam: true
        });
    }

    getCachedModificationTime(key) {
        // Simple in-memory cache - in a real system this might be persistent
        if (!this.modificationCache) {
            this.modificationCache = new Map();
        }
        return this.modificationCache.get(key) || 0;
    }

    setCachedModificationTime(key, time) {
        if (!this.modificationCache) {
            this.modificationCache = new Map();
        }
        this.modificationCache.set(key, time);
    }

    async initializeMemoryStore() {
        // Initialize memory with metadata
        const metadata = {
            initialized: new Date().toISOString(),
            version: '1.0.0',
            validators: Object.keys(this.validators),
            features: ['proactive-validation', 'comprehensive-reports', 'team-notifications']
        };

        this.validationResults.set('orchestrator:metadata', metadata);
        console.log('💾 Validation orchestrator memory store initialized');
    }

    async executeCommand(command, args) {
        return new Promise((resolve, reject) => {
            const child = spawn(command, args, {
                stdio: ['pipe', 'pipe', 'pipe']
            });

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => stdout += data);
            child.stderr.on('data', (data) => stderr += data);

            child.on('close', (code) => {
                if (code === 0) {
                    resolve(stdout);
                } else {
                    reject(new Error(`Command failed: ${stderr}`));
                }
            });
        });
    }

    // Hook handlers
    async postEditHook(data) {
        const { file } = data;

        if (file && file.endsWith('design.md')) {
            console.log(`\n📝 Design document edited: ${path.basename(file)}`);

            // Trigger validation after a delay
            setTimeout(() => {
                this.triggerComprehensiveValidation(file, 'post-edit');
            }, this.hooks.triggerDelay);
        }
    }

    async sessionRestoreHook(data) {
        console.log('🔄 Session restored - validation history available');

        if (this.validationHistory.length > 0) {
            const recent = this.validationHistory.slice(-3);
            console.log('📚 Recent validations:');
            recent.forEach(session => {
                const featureName = path.basename(path.dirname(session.designPath));
                console.log(`  ${featureName}: ${session.summary.overall} (${session.validators.join(', ')})`);
            });
        }
    }

    async sessionEndHook(data) {
        console.log('🔚 Validation session ending');

        if (this.validationHistory.length > 0) {
            const summary = {
                totalValidations: this.validationHistory.length,
                successRate: this.validationHistory.filter(s => s.summary.overall.includes('PASS')).length / this.validationHistory.length,
                averageIssueCount: this.validationHistory.reduce((sum, s) => sum + s.summary.issueCount, 0) / this.validationHistory.length,
                mostCommonValidator: this.getMostUsedValidator()
            };

            console.log('📊 Validation session summary:');
            console.log(`  Total validations: ${summary.totalValidations}`);
            console.log(`  Success rate: ${(summary.successRate * 100).toFixed(1)}%`);
            console.log(`  Average issues: ${summary.averageIssueCount.toFixed(1)}`);
            console.log(`  Most used validator: ${summary.mostCommonValidator}`);
        }
    }

    getMostUsedValidator() {
        const counts = {};
        this.validationHistory.forEach(session => {
            session.validators.forEach(validator => {
                counts[validator] = (counts[validator] || 0) + 1;
            });
        });

        return Object.entries(counts)
            .sort((a, b) => b[1] - a[1])[0]?.[0] || 'none';
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);
    const command = args[0];

    const orchestrator = new ProactiveValidationOrchestrator();

    if (command === 'init') {
        orchestrator.initialize()
            .then(() => process.exit(0))
            .catch(error => {
                console.error('Initialization failed:', error);
                process.exit(1);
            });
    } else if (command === 'validate' && args[1]) {
        const designPath = args[1];
        const validators = args[2] ? args[2].split(',') : ['design', 'taiwan', 'pdpa', 'tdd'];

        orchestrator.validateDesignDocument(designPath, { validators })
            .then(session => {
                const success = session.summary.overall.includes('PASS') ||
                              session.summary.overall.includes('COMPLIANT');
                process.exit(success ? 0 : 1);
            })
            .catch(error => {
                console.error('Validation failed:', error);
                process.exit(1);
            });
    } else if (command === 'post-edit' && args[1]) {
        const hookData = JSON.parse(args[1]);
        orchestrator.postEditHook(hookData)
            .then(() => process.exit(0))
            .catch(error => {
                console.error('Hook execution failed:', error);
                process.exit(1);
            });
    } else {
        console.log('Usage:');
        console.log('  node proactive-validation-orchestrator.js init');
        console.log('  node proactive-validation-orchestrator.js validate <design-path> [validators]');
        console.log('  node proactive-validation-orchestrator.js post-edit <hook-data>');
        console.log('');
        console.log('Validators: design,taiwan,pdpa,tdd (default: all)');
        process.exit(1);
    }
}

module.exports = ProactiveValidationOrchestrator;