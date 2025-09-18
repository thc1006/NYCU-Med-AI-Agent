#!/usr/bin/env node

/**
 * TDD Readiness Assessment Validator
 *
 * Validates design documents for Test-Driven Development readiness:
 * - Testable component architecture
 * - Clear test boundaries and interfaces
 * - Mock/stub strategies for external services
 * - Test data requirements and fixtures
 * - Coverage requirements and strategies
 * - CI/CD test integration readiness
 */

const fs = require('fs').promises;
const path = require('path');

class TDDReadinessValidator {
    constructor() {
        this.validationResults = {
            testableArchitecture: [],
            testBoundaries: [],
            mockingStrategy: [],
            testDataManagement: [],
            coverageStrategy: [],
            cicdIntegration: [],
            medicalTestSafety: [],
            strengths: []
        };

        this.tddRequirements = {
            testTypes: ['unit', 'integration', 'e2e', 'acceptance'],
            testFrameworks: ['pytest', 'jest', 'mocha', 'jasmine'],
            mockingTools: ['respx', 'mock', 'stub', 'spy', 'fake'],
            coverageTools: ['coverage', 'pytest-cov', 'istanbul', 'nyc'],
            cicdTools: ['github actions', 'jenkins', 'gitlab ci', 'azure devops'],
            testPatterns: ['arrange', 'act', 'assert', 'given', 'when', 'then']
        };

        this.medicalTestRequirements = {
            emergencyScenarios: ['chest pain', 'difficulty breathing', 'unconscious', 'severe bleeding'],
            nonEmergencyScenarios: ['headache', 'sore throat', 'minor cut', 'cold symptoms'],
            edgeCases: ['empty input', 'invalid symptoms', 'network failure', 'api timeout'],
            safetyCriteria: ['no false negatives for emergencies', 'appropriate emergency escalation', 'medical disclaimer present']
        };

        this.architecturalPatterns = {
            testable: ['dependency injection', 'interface segregation', 'single responsibility', 'pure functions'],
            problematic: ['static methods', 'global state', 'tight coupling', 'hard dependencies']
        };
    }

    async validateDocument(designPath) {
        try {
            console.log(`🧪 Validating TDD readiness for: ${path.basename(designPath)}`);

            const design = await this.loadDocument(designPath);

            // Run all TDD readiness validations
            await this.validateTestableArchitecture(design);
            await this.validateTestBoundaries(design);
            await this.validateMockingStrategy(design);
            await this.validateTestDataManagement(design);
            await this.validateCoverageStrategy(design);
            await this.validateCICDIntegration(design);
            await this.validateMedicalTestSafety(design);

            // Generate comprehensive TDD readiness report
            return this.generateTDDReport();

        } catch (error) {
            console.error('❌ TDD readiness validation failed:', error.message);
            return {
                overall: 'TDD_VALIDATION_ERROR',
                error: error.message,
                results: this.validationResults
            };
        }
    }

    async loadDocument(filePath) {
        const content = await fs.readFile(filePath, 'utf8');
        return {
            path: filePath,
            content,
            contentLower: content.toLowerCase(),
            lines: content.split('\n'),
            sections: this.extractSections(content)
        };
    }

    extractSections(content) {
        const sections = {};
        const lines = content.split('\n');
        let currentSection = null;
        let currentContent = [];

        for (const line of lines) {
            const headerMatch = line.match(/^#+\s+(.+)$/);
            if (headerMatch) {
                if (currentSection) {
                    sections[currentSection] = currentContent.join('\n').trim();
                }
                currentSection = headerMatch[1].trim();
                currentContent = [];
            } else if (currentSection) {
                currentContent.push(line);
            }
        }

        if (currentSection) {
            sections[currentSection] = currentContent.join('\n').trim();
        }

        return sections;
    }

    async validateTestableArchitecture(design) {
        console.log('🏗️ Validating testable architecture patterns...');

        const content = design.contentLower;

        // Check for dependency injection patterns
        if (!content.includes('dependency injection') && !content.includes('di') && !content.includes('inject')) {
            this.validationResults.testableArchitecture.push(
                'Dependency injection not mentioned - critical for testable architecture'
            );
        }

        // Check for interface-based design
        if (!content.includes('interface') && !content.includes('protocol') && !content.includes('abstract')) {
            this.validationResults.testableArchitecture.push(
                'Interface-based design not specified - needed for effective mocking and testing'
            );
        }

        // Check for single responsibility principle
        if (!content.includes('single responsibility') && !content.includes('srp')) {
            this.validationResults.testableArchitecture.push(
                'Single Responsibility Principle not addressed - important for focused unit tests'
            );
        }

        // Check for pure function emphasis
        if (content.includes('pure function') || content.includes('functional')) {
            this.validationResults.strengths.push(
                'Pure functional design enhances testability and predictability'
            );
        }

        // Check for problematic patterns
        const problematicPatterns = this.architecturalPatterns.problematic.filter(
            pattern => content.includes(pattern)
        );

        if (problematicPatterns.length > 0) {
            this.validationResults.testableArchitecture.push(
                `Potentially problematic patterns for testing: ${problematicPatterns.join(', ')}`
            );
        }

        // Check for component isolation
        if (!content.includes('isolat') && !content.includes('decouple')) {
            this.validationResults.testableArchitecture.push(
                'Component isolation strategy not clear - needed for independent unit testing'
            );
        }

        // Validate service layer separation
        if (content.includes('service') && content.includes('layer')) {
            this.validationResults.strengths.push(
                'Service layer separation supports testable architecture design'
            );
        }

        // Check for configuration externalization
        if (content.includes('config') && (content.includes('external') || content.includes('environment'))) {
            this.validationResults.strengths.push(
                'Externalized configuration supports test environment setup'
            );
        }
    }

    async validateTestBoundaries(design) {
        console.log('🎯 Validating test boundaries and interfaces...');

        const content = design.contentLower;

        // Check for clear API boundaries
        if (!content.includes('api') && !content.includes('endpoint') && !content.includes('interface')) {
            this.validationResults.testBoundaries.push(
                'API boundaries not clearly defined - needed for integration test scope'
            );
        }

        // Check for test types specification
        const testTypesFound = this.tddRequirements.testTypes.filter(
            type => content.includes(type)
        );

        if (testTypesFound.length < 3) {
            this.validationResults.testBoundaries.push(
                `Limited test types specified: ${testTypesFound.join(', ')} - recommend unit, integration, e2e`
            );
        } else {
            this.validationResults.strengths.push(
                `Comprehensive test types planned: ${testTypesFound.join(', ')}`
            );
        }

        // Check for test isolation boundaries
        if (!content.includes('test.*isolation') && !content.includes('independent.*test')) {
            this.validationResults.testBoundaries.push(
                'Test isolation strategy not specified - tests should run independently'
            );
        }

        // Check for contract testing
        if (content.includes('contract') && content.includes('test')) {
            this.validationResults.strengths.push(
                'Contract testing approach supports reliable service integration'
            );
        }

        // Validate component boundaries
        if (!content.includes('component.*boundary') && !content.includes('module.*boundary')) {
            this.validationResults.testBoundaries.push(
                'Component boundaries not clearly defined for focused testing'
            );
        }

        // Check for test data boundaries
        if (content.includes('test.*data') && content.includes('isolat')) {
            this.validationResults.strengths.push(
                'Test data isolation supports reliable and repeatable tests'
            );
        }
    }

    async validateMockingStrategy(design) {
        console.log('🎭 Validating mocking and stubbing strategy...');

        const content = design.contentLower;

        // Check for external service mocking
        if (content.includes('external') && (content.includes('api') || content.includes('service'))) {
            const hasMockingStrategy = this.tddRequirements.mockingTools.some(
                tool => content.includes(tool)
            );

            if (!hasMockingStrategy) {
                this.validationResults.mockingStrategy.push(
                    'External service mocking strategy not specified - critical for reliable tests'
                );
            } else {
                this.validationResults.strengths.push(
                    'External service mocking strategy planned for test reliability'
                );
            }
        }

        // Check for Google Services mocking (specific to this project)
        if (content.includes('google') && (content.includes('places') || content.includes('geocoding'))) {
            if (!content.includes('respx') && !content.includes('mock') && !content.includes('stub')) {
                this.validationResults.mockingStrategy.push(
                    'Google Services (Places, Geocoding) mocking not specified - needed to avoid API costs in tests'
                );
            }
        }

        // Check for database mocking
        if (content.includes('database') || content.includes('db')) {
            if (!content.includes('test.*database') && !content.includes('in.*memory') && !content.includes('sqlite')) {
                this.validationResults.mockingStrategy.push(
                    'Database testing strategy not clear - consider test database or in-memory options'
                );
            }
        }

        // Check for HTTP client mocking
        if (content.includes('http') && content.includes('client')) {
            if (content.includes('respx') || content.includes('httpx.*mock')) {
                this.validationResults.strengths.push(
                    'HTTP client mocking with RESpx supports external API testing'
                );
            }
        }

        // Validate fixture and factory patterns
        if (content.includes('fixture') || content.includes('factory')) {
            this.validationResults.strengths.push(
                'Test fixture/factory patterns support maintainable test data'
            );
        }

        // Check for mocking complexity management
        if (content.includes('mock.*complexity') || content.includes('simple.*mock')) {
            this.validationResults.strengths.push(
                'Mock complexity management enhances test maintainability'
            );
        }
    }

    async validateTestDataManagement(design) {
        console.log('📊 Validating test data management strategy...');

        const content = design.contentLower;

        // Check for test data strategy
        if (!content.includes('test.*data') && !content.includes('fixture') && !content.includes('seed')) {
            this.validationResults.testDataManagement.push(
                'Test data management strategy not specified'
            );
        }

        // Check for data anonymization in tests
        if (content.includes('test') && content.includes('medical')) {
            if (!content.includes('anonymous') && !content.includes('synthetic') && !content.includes('fake')) {
                this.validationResults.testDataManagement.push(
                    'Medical test data should be anonymized/synthetic to protect privacy'
                );
            } else {
                this.validationResults.strengths.push(
                    'Anonymized/synthetic medical test data protects patient privacy'
                );
            }
        }

        // Check for test data cleanup
        if (!content.includes('cleanup') && !content.includes('teardown') && !content.includes('reset')) {
            this.validationResults.testDataManagement.push(
                'Test data cleanup strategy not specified - important for test isolation'
            );
        }

        // Check for test data versioning
        if (content.includes('test.*data') && content.includes('version')) {
            this.validationResults.strengths.push(
                'Test data versioning supports reproducible tests across environments'
            );
        }

        // Validate test environment isolation
        if (content.includes('test.*environment') && content.includes('isolat')) {
            this.validationResults.strengths.push(
                'Test environment isolation prevents test interference'
            );
        }

        // Check for parameterized test data
        if (content.includes('parameteriz') || content.includes('data.*driven')) {
            this.validationResults.strengths.push(
                'Parameterized/data-driven tests increase coverage efficiency'
            );
        }
    }

    async validateCoverageStrategy(design) {
        console.log('📈 Validating test coverage strategy...');

        const content = design.contentLower;

        // Check for coverage requirements
        if (!content.includes('coverage') && !content.includes('覆蓋率')) {
            this.validationResults.coverageStrategy.push(
                'Test coverage requirements not specified'
            );
        }

        // Check for coverage targets
        const coverageTargets = content.match(/(\d+)%.*coverage|coverage.*(\d+)%/);
        if (coverageTargets) {
            const percentage = parseInt(coverageTargets[1] || coverageTargets[2]);
            if (percentage >= 90) {
                this.validationResults.strengths.push(
                    `High test coverage target (${percentage}%) supports quality assurance`
                );
            } else if (percentage < 80) {
                this.validationResults.coverageStrategy.push(
                    `Low coverage target (${percentage}%) - recommend 90%+ for medical applications`
                );
            }
        }

        // Check for coverage tools
        const coverageToolsFound = this.tddRequirements.coverageTools.filter(
            tool => content.includes(tool)
        );

        if (coverageToolsFound.length === 0) {
            this.validationResults.coverageStrategy.push(
                'Coverage measurement tools not specified (pytest-cov, coverage, etc.)'
            );
        }

        // Check for branch coverage
        if (content.includes('branch.*coverage') || content.includes('conditional.*coverage')) {
            this.validationResults.strengths.push(
                'Branch/conditional coverage provides thorough test validation'
            );
        }

        // Check for critical path coverage
        if (content.includes('critical.*path') || content.includes('emergency.*path')) {
            this.validationResults.strengths.push(
                'Critical path coverage ensures emergency scenarios are thoroughly tested'
            );
        }

        // Validate coverage reporting
        if (content.includes('coverage.*report') || content.includes('coverage.*dashboard')) {
            this.validationResults.strengths.push(
                'Coverage reporting supports continuous quality monitoring'
            );
        }
    }

    async validateCICDIntegration(design) {
        console.log('🔄 Validating CI/CD test integration...');

        const content = design.contentLower;

        // Check for CI/CD platform
        const cicdToolsFound = this.tddRequirements.cicdTools.filter(
            tool => content.includes(tool)
        );

        if (cicdToolsFound.length === 0) {
            this.validationResults.cicdIntegration.push(
                'CI/CD platform not specified for automated testing'
            );
        }

        // Check for automated test execution
        if (!content.includes('automat.*test') && !content.includes('continuous.*test')) {
            this.validationResults.cicdIntegration.push(
                'Automated test execution in CI/CD not specified'
            );
        }

        // Check for test failure handling
        if (!content.includes('test.*fail') && !content.includes('build.*break')) {
            this.validationResults.cicdIntegration.push(
                'Test failure handling strategy not specified'
            );
        }

        // Check for test result reporting
        if (content.includes('test.*report') || content.includes('junit') || content.includes('test.*result')) {
            this.validationResults.strengths.push(
                'Test result reporting supports continuous quality monitoring'
            );
        }

        // Check for quality gates
        if (content.includes('quality.*gate') || content.includes('gate.*check')) {
            this.validationResults.strengths.push(
                'Quality gates prevent defective code from reaching production'
            );
        }

        // Validate parallel test execution
        if (content.includes('parallel.*test') || content.includes('concurrent.*test')) {
            this.validationResults.strengths.push(
                'Parallel test execution optimizes CI/CD pipeline performance'
            );
        }

        // Check for test environment provisioning
        if (content.includes('test.*environment') && content.includes('provision')) {
            this.validationResults.strengths.push(
                'Automated test environment provisioning supports reliable testing'
            );
        }
    }

    async validateMedicalTestSafety(design) {
        console.log('🏥 Validating medical-specific test safety requirements...');

        const content = design.contentLower;

        // Check for emergency scenario testing
        const emergencyTestCoverage = this.medicalTestRequirements.emergencyScenarios.filter(
            scenario => content.includes(scenario)
        );

        if (emergencyTestCoverage.length === 0) {
            this.validationResults.medicalTestSafety.push(
                'Emergency scenario testing not specified - critical for medical safety'
            );
        } else {
            this.validationResults.strengths.push(
                `Emergency scenarios planned for testing: ${emergencyTestCoverage.join(', ')}`
            );
        }

        // Check for false negative prevention testing
        if (!content.includes('false.*negative') && !content.includes('miss.*emergency')) {
            this.validationResults.medicalTestSafety.push(
                'False negative testing not specified - critical to avoid missing emergencies'
            );
        }

        // Check for medical disclaimer testing
        if (!content.includes('disclaimer.*test') && !content.includes('test.*disclaimer')) {
            this.validationResults.medicalTestSafety.push(
                'Medical disclaimer presence testing not specified'
            );
        }

        // Check for Taiwan emergency number testing
        if (content.includes('119') && content.includes('test')) {
            this.validationResults.strengths.push(
                'Taiwan emergency number (119) integration testing planned'
            );
        }

        // Check for edge case testing
        const edgeCaseCoverage = this.medicalTestRequirements.edgeCases.filter(
            edgeCase => content.includes(edgeCase)
        );

        if (edgeCaseCoverage.length < 2) {
            this.validationResults.medicalTestSafety.push(
                'Limited edge case testing - important for medical application robustness'
            );
        }

        // Check for accessibility testing
        if (content.includes('accessibility.*test') || content.includes('a11y')) {
            this.validationResults.strengths.push(
                'Accessibility testing ensures medical information reaches all users'
            );
        }

        // Validate stress testing for emergency load
        if (content.includes('stress.*test') || content.includes('load.*test')) {
            this.validationResults.strengths.push(
                'Stress/load testing ensures system reliability during emergencies'
            );
        }

        // Check for medical data privacy in tests
        if (content.includes('privacy.*test') || content.includes('pdpa.*test')) {
            this.validationResults.strengths.push(
                'Privacy compliance testing supports PDPA requirements'
            );
        }
    }

    generateTDDReport() {
        const categories = Object.keys(this.validationResults).filter(key => key !== 'strengths');
        const totalIssues = categories.reduce((sum, key) => sum + this.validationResults[key].length, 0);
        const totalStrengths = this.validationResults.strengths.length;

        let overallRating;
        let readinessScore;

        if (totalIssues === 0) {
            overallRating = 'TDD_FULLY_READY';
            readinessScore = 100;
        } else if (totalIssues <= 3) {
            overallRating = 'TDD_MOSTLY_READY';
            readinessScore = 85;
        } else if (totalIssues <= 6) {
            overallRating = 'TDD_NEEDS_PREPARATION';
            readinessScore = 65;
        } else {
            overallRating = 'TDD_MAJOR_GAPS';
            readinessScore = 35;
        }

        const report = {
            timestamp: new Date().toISOString(),
            overall: overallRating,
            readinessScore,
            summary: this.generateReadinessSummary(overallRating, totalIssues, totalStrengths),
            breakdown: {
                testableArchitecture: this.validationResults.testableArchitecture,
                testBoundaries: this.validationResults.testBoundaries,
                mockingStrategy: this.validationResults.mockingStrategy,
                testDataManagement: this.validationResults.testDataManagement,
                coverageStrategy: this.validationResults.coverageStrategy,
                cicdIntegration: this.validationResults.cicdIntegration,
                medicalTestSafety: this.validationResults.medicalTestSafety,
                strengths: this.validationResults.strengths
            },
            readinessMatrix: this.generateReadinessMatrix(),
            recommendations: this.generateTDDRecommendations(),
            implementationRoadmap: this.generateImplementationRoadmap()
        };

        this.printTDDReport(report);
        return report;
    }

    generateReadinessSummary(rating, issues, strengths) {
        switch (rating) {
            case 'TDD_FULLY_READY':
                return `🧪 Fully TDD-ready with ${strengths} testing strengths identified`;
            case 'TDD_MOSTLY_READY':
                return `🧪 Strong TDD readiness with ${issues} minor gaps and ${strengths} strengths`;
            case 'TDD_NEEDS_PREPARATION':
                return `🧪 TDD implementation needs preparation: ${issues} gaps to address`;
            case 'TDD_MAJOR_GAPS':
                return `🧪 Major TDD readiness gaps: ${issues} critical issues require attention`;
            default:
                return 'TDD readiness validation completed';
        }
    }

    generateReadinessMatrix() {
        return {
            testableArchitecture: this.validationResults.testableArchitecture.length === 0,
            testBoundaries: this.validationResults.testBoundaries.length === 0,
            mockingStrategy: this.validationResults.mockingStrategy.length === 0,
            testDataManagement: this.validationResults.testDataManagement.length === 0,
            coverageStrategy: this.validationResults.coverageStrategy.length === 0,
            cicdIntegration: this.validationResults.cicdIntegration.length === 0,
            medicalTestSafety: this.validationResults.medicalTestSafety.length === 0
        };
    }

    generateTDDRecommendations() {
        const recommendations = [];

        if (this.validationResults.testableArchitecture.length > 0) {
            recommendations.push({
                category: 'Architecture',
                priority: 'High',
                action: 'Refactor design to support dependency injection and interface-based testing',
                timeline: 'Before implementation'
            });
        }

        if (this.validationResults.mockingStrategy.length > 0) {
            recommendations.push({
                category: 'Mocking',
                priority: 'High',
                action: 'Define comprehensive mocking strategy for external services (Google APIs, etc.)',
                timeline: 'Before writing tests'
            });
        }

        if (this.validationResults.medicalTestSafety.length > 0) {
            recommendations.push({
                category: 'Medical Safety',
                priority: 'Critical',
                action: 'Develop comprehensive emergency scenario and false negative prevention tests',
                timeline: 'First priority'
            });
        }

        if (this.validationResults.coverageStrategy.length > 0) {
            recommendations.push({
                category: 'Coverage',
                priority: 'Medium',
                action: 'Establish coverage requirements (90%+) and measurement tools',
                timeline: 'During test setup'
            });
        }

        if (this.validationResults.cicdIntegration.length > 0) {
            recommendations.push({
                category: 'CI/CD',
                priority: 'Medium',
                action: 'Setup automated testing pipeline with quality gates',
                timeline: 'During development setup'
            });
        }

        return recommendations;
    }

    generateImplementationRoadmap() {
        return {
            phase1: {
                name: 'Test Infrastructure Setup',
                tasks: [
                    'Setup pytest with coverage reporting',
                    'Configure RESpx for HTTP mocking',
                    'Create test database strategy',
                    'Establish test data fixtures'
                ],
                duration: '1-2 weeks'
            },
            phase2: {
                name: 'Core TDD Implementation',
                tasks: [
                    'Implement dependency injection patterns',
                    'Create service layer interfaces',
                    'Write comprehensive unit tests',
                    'Establish integration test boundaries'
                ],
                duration: '2-3 weeks'
            },
            phase3: {
                name: 'Medical Safety Testing',
                tasks: [
                    'Develop emergency scenario tests',
                    'Implement false negative prevention tests',
                    'Create Taiwan emergency protocol tests',
                    'Validate medical disclaimer testing'
                ],
                duration: '1-2 weeks'
            },
            phase4: {
                name: 'CI/CD Integration',
                tasks: [
                    'Setup automated test execution',
                    'Configure coverage reporting',
                    'Implement quality gates',
                    'Setup test result notifications'
                ],
                duration: '1 week'
            }
        };
    }

    printTDDReport(report) {
        console.log('\n🧪 TDD READINESS VALIDATION REPORT');
        console.log('='.repeat(55));
        console.log(`Overall Rating: ${report.overall}`);
        console.log(`Readiness Score: ${report.readinessScore}%`);
        console.log(`Summary: ${report.summary}`);
        console.log('');

        console.log('📊 TDD Readiness Matrix:');
        Object.entries(report.readinessMatrix).forEach(([area, ready]) => {
            const status = ready ? '✅' : '❌';
            const displayName = area.replace(/([A-Z])/g, ' $1').toLowerCase();
            console.log(`  ${status} ${displayName.charAt(0).toUpperCase() + displayName.slice(1)}`);
        });

        console.log('');
        console.log('⚠️  TDD Readiness Gaps:');
        Object.entries(report.breakdown).forEach(([category, issues]) => {
            if (category !== 'strengths' && issues.length > 0) {
                const displayName = category.replace(/([A-Z])/g, ' $1').toLowerCase();
                console.log(`  ${displayName}: ${issues.length} gaps`);
                issues.forEach(issue => console.log(`    - ${issue}`));
            }
        });

        console.log('');
        console.log('💪 TDD Strengths:');
        report.breakdown.strengths.forEach(strength => {
            console.log(`  + ${strength}`);
        });

        if (report.recommendations.length > 0) {
            console.log('');
            console.log('📋 TDD Implementation Recommendations:');
            report.recommendations.forEach(rec => {
                console.log(`  [${rec.priority}] ${rec.category}: ${rec.action}`);
                console.log(`    Timeline: ${rec.timeline}`);
            });
        }

        console.log('');
        console.log('🗺️ Implementation Roadmap:');
        Object.entries(report.implementationRoadmap).forEach(([phase, details]) => {
            console.log(`  ${phase.toUpperCase()}: ${details.name} (${details.duration})`);
            details.tasks.forEach(task => console.log(`    • ${task}`));
        });

        console.log('='.repeat(55));
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);

    if (args.length < 1) {
        console.log('Usage: node tdd-readiness-validator.js <design-path>');
        console.log('');
        console.log('Validates design documents for TDD readiness:');
        console.log('  - Testable architecture patterns');
        console.log('  - Clear test boundaries and interfaces');
        console.log('  - Mocking strategy for external services');
        console.log('  - Test data management and fixtures');
        console.log('  - Coverage requirements and measurement');
        console.log('  - CI/CD test integration readiness');
        console.log('  - Medical-specific test safety requirements');
        process.exit(1);
    }

    const validator = new TDDReadinessValidator();
    validator.validateDocument(args[0])
        .then(report => {
            const success = report.overall.includes('READY');
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('❌ TDD readiness validation failed:', error);
            process.exit(1);
        });
}

module.exports = TDDReadinessValidator;