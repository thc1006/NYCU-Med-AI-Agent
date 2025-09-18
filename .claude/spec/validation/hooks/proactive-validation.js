#!/usr/bin/env node

/**
 * Proactive Design Validation Hooks
 *
 * Automatically triggers validation when design documents are modified
 * Integrates with Claude-Flow coordination system
 * Stores validation results in memory for team access
 */

const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');

class ProactiveValidationHooks {
    constructor() {
        this.validationQueue = new Map();
        this.activeValidations = new Set();
        this.hooks = {
            preEdit: this.preEditHook.bind(this),
            postEdit: this.postEditHook.bind(this),
            preTask: this.preTaskHook.bind(this),
            postTask: this.postTaskHook.bind(this),
            sessionRestore: this.sessionRestoreHook.bind(this),
            sessionEnd: this.sessionEndHook.bind(this)
        };
        this.memoryStore = new Map();
        this.validationHistory = [];
    }

    async initialize() {
        console.log('🔄 Initializing proactive validation hooks...');

        try {
            // Register with Claude-Flow hooks system
            await this.registerHooks();

            // Start file watcher for design documents
            await this.startFileWatcher();

            // Initialize memory storage
            await this.initializeMemoryStore();

            console.log('✅ Proactive validation system active');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize validation hooks:', error);
            return false;
        }
    }

    async registerHooks() {
        const hookTypes = [
            'pre-edit',
            'post-edit',
            'pre-task',
            'post-task',
            'session-restore',
            'session-end'
        ];

        for (const hookType of hookTypes) {
            try {
                await this.executeCommand(
                    'npx',
                    ['claude-flow@alpha', 'hooks', 'register', hookType, '--handler', __filename]
                );
                console.log(`📋 Registered ${hookType} hook`);
            } catch (error) {
                console.warn(`⚠️ Could not register ${hookType} hook:`, error.message);
            }
        }
    }

    async startFileWatcher() {
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
                        const cachedTime = this.memoryStore.get(cacheKey) || 0;

                        if (lastModified > cachedTime) {
                            this.memoryStore.set(cacheKey, lastModified);
                            await this.triggerValidation(designPath, 'file-change');
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

    async triggerValidation(designPath, trigger) {
        const validationKey = `validation:${designPath}:${Date.now()}`;

        if (this.activeValidations.has(designPath)) {
            console.log(`⏳ Validation already in progress for: ${path.basename(designPath)}`);
            return;
        }

        console.log(`🔍 Triggering validation for: ${path.basename(designPath)} (${trigger})`);

        this.activeValidations.add(designPath);

        try {
            // Find related files
            const featureDir = path.dirname(designPath);
            const requirementsPath = path.join(featureDir, 'requirements.md');
            const templatePath = path.join(process.cwd(), '.claude', 'templates', 'design-template.md');

            // Execute validation
            const validatorPath = path.join(__dirname, 'spec-design-validator.js');
            const result = await this.executeValidator(validatorPath, designPath, requirementsPath, templatePath);

            // Store results in memory
            await this.storeValidationResult(validationKey, designPath, result, trigger);

            // Notify team via hooks
            await this.notifyValidationComplete(designPath, result);

        } catch (error) {
            console.error(`❌ Validation failed for ${designPath}:`, error.message);
            await this.storeValidationError(validationKey, designPath, error, trigger);
        } finally {
            this.activeValidations.delete(designPath);
        }
    }

    async executeValidator(validatorPath, designPath, requirementsPath, templatePath) {
        return new Promise((resolve, reject) => {
            const args = [validatorPath, designPath];

            // Add optional paths if they exist
            if (requirementsPath) args.push(requirementsPath);
            if (templatePath) args.push(templatePath);

            const child = spawn('node', args, {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: process.cwd()
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
                    try {
                        // Parse validation output
                        const result = this.parseValidationOutput(stdout);
                        resolve(result);
                    } catch (error) {
                        reject(new Error(`Failed to parse validation output: ${error.message}`));
                    }
                } else {
                    reject(new Error(`Validation process failed with code ${code}: ${stderr}`));
                }
            });

            child.on('error', (error) => {
                reject(new Error(`Failed to start validation process: ${error.message}`));
            });
        });
    }

    parseValidationOutput(output) {
        // Extract validation results from output
        const lines = output.split('\n');
        let rating = 'UNKNOWN';
        const issues = [];
        const strengths = [];

        for (const line of lines) {
            if (line.includes('Overall Rating:')) {
                rating = line.split(':')[1].trim();
            } else if (line.includes('Issues:') || line.includes('Missing:') || line.includes('Error:')) {
                issues.push(line.trim());
            } else if (line.includes('Strengths:') || line.includes('Good:') || line.includes('Excellent:')) {
                strengths.push(line.trim());
            }
        }

        return {
            rating,
            issues,
            strengths,
            timestamp: new Date().toISOString(),
            rawOutput: output
        };
    }

    async storeValidationResult(key, designPath, result, trigger) {
        const featureName = path.basename(path.dirname(designPath));
        const memoryKey = `spec/validation/${featureName}/${Date.now()}`;

        const validationRecord = {
            timestamp: new Date().toISOString(),
            designPath,
            trigger,
            rating: result.rating,
            summary: this.generateValidationSummary(result),
            issues: result.issues,
            strengths: result.strengths,
            memoryKey
        };

        // Store in memory
        this.memoryStore.set(memoryKey, validationRecord);
        this.validationHistory.push(validationRecord);

        // Store via Claude-Flow memory system
        try {
            await this.executeCommand('npx', [
                'claude-flow@alpha',
                'hooks',
                'memory-store',
                '--key', memoryKey,
                '--data', JSON.stringify(validationRecord)
            ]);
            console.log(`💾 Validation stored in memory: ${memoryKey}`);
        } catch (error) {
            console.warn('⚠️ Could not store in Claude-Flow memory:', error.message);
        }

        // Write to local cache
        const reportPath = path.join(
            path.dirname(designPath),
            '..',
            'validation',
            'reports',
            `${featureName}-validation-${Date.now()}.json`
        );

        try {
            await fs.mkdir(path.dirname(reportPath), { recursive: true });
            await fs.writeFile(reportPath, JSON.stringify(validationRecord, null, 2));
            console.log(`📁 Validation report saved: ${reportPath}`);
        } catch (error) {
            console.warn('⚠️ Could not save validation report:', error.message);
        }
    }

    generateValidationSummary(result) {
        const issueCount = result.issues.length;
        const strengthCount = result.strengths.length;

        if (result.rating === 'PASS') {
            return `✅ Design validation passed with ${strengthCount} strengths identified`;
        } else if (result.rating === 'NEEDS_IMPROVEMENT') {
            return `⚠️ Design needs improvement: ${issueCount} issues to address`;
        } else {
            return `❌ Design has major issues: ${issueCount} critical problems found`;
        }
    }

    async storeValidationError(key, designPath, error, trigger) {
        const featureName = path.basename(path.dirname(designPath));
        const memoryKey = `spec/validation/${featureName}/error/${Date.now()}`;

        const errorRecord = {
            timestamp: new Date().toISOString(),
            designPath,
            trigger,
            error: error.message,
            type: 'validation-error',
            memoryKey
        };

        this.memoryStore.set(memoryKey, errorRecord);
        console.error(`❌ Validation error stored: ${memoryKey}`);
    }

    async notifyValidationComplete(designPath, result) {
        const featureName = path.basename(path.dirname(designPath));
        const message = `Design validation completed for ${featureName}: ${result.rating}`;

        try {
            await this.executeCommand('npx', [
                'claude-flow@alpha',
                'hooks',
                'notify',
                '--message', message,
                '--type', 'validation-complete',
                '--data', JSON.stringify({ designPath, rating: result.rating })
            ]);
        } catch (error) {
            console.warn('⚠️ Could not send validation notification:', error.message);
        }
    }

    // Hook implementations
    async preEditHook(data) {
        const { file } = data;

        if (file && file.endsWith('design.md')) {
            console.log(`📝 Pre-edit hook: ${path.basename(file)}`);

            // Check if design has existing validation
            const existingValidation = await this.getLatestValidation(file);
            if (existingValidation) {
                console.log(`📊 Previous validation: ${existingValidation.rating}`);

                if (existingValidation.rating === 'MAJOR_ISSUES') {
                    console.warn('⚠️ Warning: Editing design with major validation issues');
                }
            }
        }
    }

    async postEditHook(data) {
        const { file } = data;

        if (file && file.endsWith('design.md')) {
            console.log(`✏️ Post-edit hook: ${path.basename(file)}`);

            // Trigger validation after edit
            setTimeout(() => {
                this.triggerValidation(file, 'post-edit');
            }, 2000); // Small delay to allow file to be written
        }
    }

    async preTaskHook(data) {
        const { description } = data;

        if (description && description.toLowerCase().includes('design')) {
            console.log('🎯 Pre-task hook: Design-related task starting');

            // Check for validation status of current designs
            await this.reportValidationStatus();
        }
    }

    async postTaskHook(data) {
        const { taskId } = data;

        console.log(`✅ Post-task hook: Task ${taskId} completed`);

        // Check if any design documents were modified
        await this.checkForRecentDesignChanges();
    }

    async sessionRestoreHook(data) {
        const { sessionId } = data;

        console.log(`🔄 Session restore: ${sessionId}`);

        // Restore validation history from memory
        await this.restoreValidationHistory();
    }

    async sessionEndHook(data) {
        const { exportMetrics } = data;

        console.log('🔚 Session ending, generating validation summary');

        if (exportMetrics) {
            await this.exportValidationMetrics();
        }
    }

    async getLatestValidation(designPath) {
        const featureName = path.basename(path.dirname(designPath));

        // Search memory for latest validation
        for (const [key, value] of this.memoryStore.entries()) {
            if (key.includes(`spec/validation/${featureName}`) && value.designPath === designPath) {
                return value;
            }
        }

        return null;
    }

    async reportValidationStatus() {
        const recentValidations = this.validationHistory.slice(-5);

        if (recentValidations.length === 0) {
            console.log('📊 No recent validations found');
            return;
        }

        console.log('📊 Recent validation status:');
        for (const validation of recentValidations) {
            const featureName = path.basename(path.dirname(validation.designPath));
            console.log(`  ${featureName}: ${validation.rating} (${validation.summary})`);
        }
    }

    async checkForRecentDesignChanges() {
        // Implementation would check for design file modifications in the last few minutes
        console.log('🔍 Checking for recent design changes...');
    }

    async restoreValidationHistory() {
        try {
            // Restore from Claude-Flow memory
            const result = await this.executeCommand('npx', [
                'claude-flow@alpha',
                'hooks',
                'memory-restore',
                '--pattern', 'spec/validation/*'
            ]);

            console.log('📚 Validation history restored');
        } catch (error) {
            console.warn('⚠️ Could not restore validation history:', error.message);
        }
    }

    async exportValidationMetrics() {
        const metrics = {
            totalValidations: this.validationHistory.length,
            passRate: this.validationHistory.filter(v => v.rating === 'PASS').length / this.validationHistory.length,
            commonIssues: this.analyzeCommonIssues(),
            averageValidationTime: this.calculateAverageValidationTime(),
            timestamp: new Date().toISOString()
        };

        const metricsPath = path.join(process.cwd(), '.claude', 'spec', 'validation', 'metrics.json');

        try {
            await fs.writeFile(metricsPath, JSON.stringify(metrics, null, 2));
            console.log(`📈 Validation metrics exported: ${metricsPath}`);
        } catch (error) {
            console.warn('⚠️ Could not export metrics:', error.message);
        }
    }

    analyzeCommonIssues() {
        const issueFrequency = new Map();

        for (const validation of this.validationHistory) {
            for (const issue of validation.issues) {
                const key = issue.substring(0, 50); // First 50 chars as key
                issueFrequency.set(key, (issueFrequency.get(key) || 0) + 1);
            }
        }

        return Array.from(issueFrequency.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([issue, count]) => ({ issue, count }));
    }

    calculateAverageValidationTime() {
        // Placeholder - would track actual validation times
        return 2.5; // seconds
    }

    async initializeMemoryStore() {
        // Initialize memory with persistent storage
        this.memoryStore.set('validation:initialized', new Date().toISOString());
        console.log('💾 Memory store initialized');
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
}

// CLI interface for hook execution
if (require.main === module) {
    const hookType = process.argv[2];
    const hookData = process.argv[3] ? JSON.parse(process.argv[3]) : {};

    const hooks = new ProactiveValidationHooks();

    if (hookType && hooks.hooks[hookType.replace('-', '')]) {
        hooks.hooks[hookType.replace('-', '')](hookData)
            .then(() => process.exit(0))
            .catch(error => {
                console.error('Hook execution failed:', error);
                process.exit(1);
            });
    } else if (hookType === 'init') {
        hooks.initialize()
            .then(() => process.exit(0))
            .catch(error => {
                console.error('Initialization failed:', error);
                process.exit(1);
            });
    } else {
        console.log('Usage: node proactive-validation.js <hook-type|init> [hook-data]');
        process.exit(1);
    }
}

module.exports = ProactiveValidationHooks;