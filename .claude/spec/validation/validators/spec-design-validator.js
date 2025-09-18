#!/usr/bin/env node

/**
 * Spec Design Validator - Taiwan Medical AI Agent
 *
 * Validates technical design documents for:
 * - Template compliance
 * - Requirements coverage
 * - Technical soundness
 * - Medical safety compliance
 * - Taiwan localization
 * - PDPA privacy compliance
 */

const fs = require('fs').promises;
const path = require('path');

class SpecDesignValidator {
    constructor() {
        this.validationResults = {
            overall: 'PENDING',
            templateCompliance: [],
            requirementsCoverage: [],
            requirementsAlignment: [],
            technicalIssues: [],
            integrationGaps: [],
            documentationIssues: [],
            improvementSuggestions: [],
            strengths: []
        };

        this.requiredTemplateSections = [
            'Overview',
            'Architecture',
            'Components',
            'Data Models',
            'Error Handling',
            'Testing Strategy'
        ];

        this.taiwanEmergencyNumbers = ['119', '110', '112', '113', '165'];
        this.requiredMedicalDisclaimers = [
            '本系統僅供一般資訊',
            '非醫療診斷',
            '緊急狀況請撥打',
            '119',
            '112'
        ];
    }

    async validateDesign(designPath, requirementsPath, templatePath) {
        try {
            console.log(`🔍 Starting validation for: ${designPath}`);

            // Load documents
            const design = await this.loadDocument(designPath);
            const requirements = requirementsPath ? await this.loadDocument(requirementsPath) : null;
            const template = templatePath ? await this.loadDocument(templatePath) : null;

            // Run all validations
            await this.validateTemplateCompliance(design, template);
            await this.validateRequirementsCoverage(design, requirements);
            await this.validateRequirementsAlignment(design, requirements);
            await this.validateTechnicalSoundness(design);
            await this.validateMedicalSafety(design);
            await this.validateTaiwanLocalization(design);
            await this.validatePDPACompliance(design);
            await this.validateDocumentationQuality(design);
            await this.validateTDDReadiness(design);

            // Calculate overall rating
            this.calculateOverallRating();

            // Store results in memory
            await this.storeValidationResults(designPath);

            // Generate report
            return this.generateReport();

        } catch (error) {
            console.error('❌ Validation failed:', error.message);
            this.validationResults.overall = 'MAJOR_ISSUES';
            this.validationResults.technicalIssues.push(`Validation error: ${error.message}`);
            return this.generateReport();
        }
    }

    async loadDocument(filePath) {
        try {
            const content = await fs.readFile(filePath, 'utf8');
            return {
                path: filePath,
                content,
                sections: this.extractSections(content),
                diagrams: this.extractMermaidDiagrams(content)
            };
        } catch (error) {
            throw new Error(`Cannot load document: ${filePath} - ${error.message}`);
        }
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

    extractMermaidDiagrams(content) {
        const mermaidRegex = /```mermaid\n([\s\S]*?)\n```/g;
        const diagrams = [];
        let match;

        while ((match = mermaidRegex.exec(content)) !== null) {
            diagrams.push({
                type: this.detectDiagramType(match[1]),
                content: match[1].trim()
            });
        }

        return diagrams;
    }

    detectDiagramType(content) {
        if (content.includes('graph') || content.includes('flowchart')) return 'flowchart';
        if (content.includes('sequenceDiagram')) return 'sequence';
        if (content.includes('erDiagram')) return 'entity-relationship';
        if (content.includes('classDiagram')) return 'class';
        return 'unknown';
    }

    async validateTemplateCompliance(design, template) {
        console.log('📋 Validating template compliance...');

        // Check required sections
        const missingSections = this.requiredTemplateSections.filter(
            section => !Object.keys(design.sections).some(s => s.toLowerCase().includes(section.toLowerCase()))
        );

        if (missingSections.length > 0) {
            this.validationResults.templateCompliance.push(
                `Missing required sections: ${missingSections.join(', ')}`
            );
        }

        // Check Mermaid diagrams
        if (design.diagrams.length === 0) {
            this.validationResults.templateCompliance.push(
                'No Mermaid diagrams found - architecture diagrams are required'
            );
        }

        // Validate diagram types for medical AI
        const requiredDiagramTypes = ['flowchart', 'sequence'];
        const presentDiagramTypes = design.diagrams.map(d => d.type);
        const missingDiagramTypes = requiredDiagramTypes.filter(
            type => !presentDiagramTypes.includes(type)
        );

        if (missingDiagramTypes.length > 0) {
            this.validationResults.templateCompliance.push(
                `Missing required diagram types: ${missingDiagramTypes.join(', ')}`
            );
        }

        if (this.validationResults.templateCompliance.length === 0) {
            this.validationResults.strengths.push('Excellent template compliance with all required sections');
        }
    }

    async validateRequirementsCoverage(design, requirements) {
        if (!requirements) {
            this.validationResults.requirementsCoverage.push(
                'No requirements document provided for coverage validation'
            );
            return;
        }

        console.log('📊 Validating requirements coverage...');

        // Extract requirements from requirements document
        const reqList = this.extractRequirements(requirements.content);
        const designContent = design.content.toLowerCase();

        const uncoveredRequirements = reqList.filter(req => {
            const keywords = this.extractKeywords(req);
            return !keywords.some(keyword => designContent.includes(keyword.toLowerCase()));
        });

        if (uncoveredRequirements.length > 0) {
            this.validationResults.requirementsCoverage.push(
                `Uncovered requirements: ${uncoveredRequirements.map(r => r.substring(0, 50) + '...').join('; ')}`
            );
        } else {
            this.validationResults.strengths.push('Complete requirements coverage achieved');
        }
    }

    async validateRequirementsAlignment(design, requirements) {
        if (!requirements) return;

        console.log('🎯 Validating requirements alignment...');

        // Check for acceptance criteria alignment
        const acceptanceCriteria = this.extractAcceptanceCriteria(requirements.content);
        const designSolutions = this.extractDesignSolutions(design.content);

        const misalignedCriteria = acceptanceCriteria.filter(criteria => {
            return !designSolutions.some(solution =>
                this.checkAlignmentMatch(criteria, solution)
            );
        });

        if (misalignedCriteria.length > 0) {
            this.validationResults.requirementsAlignment.push(
                `Design solutions don't align with acceptance criteria: ${misalignedCriteria.length} items`
            );
        }
    }

    extractRequirements(content) {
        // Extract bullet points and numbered lists as requirements
        const lines = content.split('\n');
        return lines.filter(line =>
            line.trim().match(/^[-*+]\s+/) ||
            line.trim().match(/^\d+\.\s+/) ||
            line.toLowerCase().includes('must') ||
            line.toLowerCase().includes('shall') ||
            line.toLowerCase().includes('should')
        ).map(line => line.trim());
    }

    extractKeywords(requirement) {
        // Extract meaningful keywords from requirement text
        const words = requirement.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word =>
                word.length > 3 &&
                !['must', 'shall', 'should', 'will', 'the', 'and', 'or', 'but', 'for', 'with'].includes(word)
            );
        return words;
    }

    extractAcceptanceCriteria(content) {
        const lines = content.split('\n');
        return lines.filter(line =>
            line.toLowerCase().includes('acceptance') ||
            line.toLowerCase().includes('criteria') ||
            line.toLowerCase().includes('given') ||
            line.toLowerCase().includes('when') ||
            line.toLowerCase().includes('then')
        );
    }

    extractDesignSolutions(content) {
        const lines = content.split('\n');
        return lines.filter(line =>
            line.toLowerCase().includes('implementation') ||
            line.toLowerCase().includes('solution') ||
            line.toLowerCase().includes('approach') ||
            line.toLowerCase().includes('design')
        );
    }

    checkAlignmentMatch(criteria, solution) {
        const criteriaWords = this.extractKeywords(criteria);
        const solutionWords = this.extractKeywords(solution);

        // Check if at least 30% of criteria keywords appear in solution
        const matchCount = criteriaWords.filter(word =>
            solutionWords.some(sWord => sWord.includes(word) || word.includes(sWord))
        ).length;

        return (matchCount / criteriaWords.length) >= 0.3;
    }

    async validateTechnicalSoundness(design) {
        console.log('🔧 Validating technical soundness...');

        const content = design.content.toLowerCase();

        // Check for FastAPI patterns
        if (!content.includes('fastapi') && !content.includes('rest') && !content.includes('api')) {
            this.validationResults.technicalIssues.push(
                'No FastAPI or REST API design patterns mentioned'
            );
        }

        // Check for database design
        if (!content.includes('database') && !content.includes('postgresql') && !content.includes('sqlite')) {
            this.validationResults.technicalIssues.push(
                'Database design not specified or unclear'
            );
        }

        // Check for authentication/security
        if (!content.includes('auth') && !content.includes('security') && !content.includes('jwt')) {
            this.validationResults.technicalIssues.push(
                'Authentication and security considerations not addressed'
            );
        }

        // Check for error handling
        if (!content.includes('error') && !content.includes('exception') && !content.includes('failure')) {
            this.validationResults.technicalIssues.push(
                'Error handling strategy not defined'
            );
        }

        // Check for performance considerations
        if (!content.includes('performance') && !content.includes('scale') && !content.includes('cache')) {
            this.validationResults.technicalIssues.push(
                'Performance and scalability considerations missing'
            );
        }
    }

    async validateMedicalSafety(design) {
        console.log('🏥 Validating medical safety compliance...');

        const content = design.content;

        // Check for Taiwan emergency numbers
        const missingEmergencyNumbers = this.taiwanEmergencyNumbers.filter(
            number => !content.includes(number)
        );

        if (missingEmergencyNumbers.length > 0) {
            this.validationResults.technicalIssues.push(
                `Missing Taiwan emergency numbers: ${missingEmergencyNumbers.join(', ')}`
            );
        }

        // Check for medical disclaimers
        const missingDisclaimers = this.requiredMedicalDisclaimers.filter(
            disclaimer => !content.includes(disclaimer)
        );

        if (missingDisclaimers.length > 0) {
            this.validationResults.technicalIssues.push(
                'Missing required medical disclaimers and emergency guidance'
            );
        }

        // Check for diagnostic language (should not be present)
        const diagnosticTerms = ['diagnose', 'diagnosis', 'prescribe', 'prescription', 'treat', 'treatment', 'cure'];
        const foundDiagnosticTerms = diagnosticTerms.filter(term => content.toLowerCase().includes(term));

        if (foundDiagnosticTerms.length > 0) {
            this.validationResults.technicalIssues.push(
                `Contains inappropriate diagnostic language: ${foundDiagnosticTerms.join(', ')}`
            );
        }

        // Check for emergency escalation
        if (!content.includes('emergency') || !content.includes('escalation')) {
            this.validationResults.technicalIssues.push(
                'Emergency escalation protocols not clearly defined'
            );
        }
    }

    async validateTaiwanLocalization(design) {
        console.log('🇹🇼 Validating Taiwan localization...');

        const content = design.content;

        // Check for zh-TW language specification
        if (!content.includes('zh-TW') && !content.includes('zh_TW')) {
            this.validationResults.technicalIssues.push(
                'Traditional Chinese (zh-TW) language specification missing'
            );
        }

        // Check for Taiwan region code
        if (!content.includes('TW') && !content.includes('Taiwan')) {
            this.validationResults.technicalIssues.push(
                'Taiwan region code (TW) specification missing'
            );
        }

        // Check for Taiwan healthcare system integration
        const taiwanHealthcareTerms = ['健保', 'MOHW', '衛生福利部', '健保署', 'NHI'];
        const foundHealthcareTerms = taiwanHealthcareTerms.filter(term => content.includes(term));

        if (foundHealthcareTerms.length === 0) {
            this.validationResults.technicalIssues.push(
                'Taiwan healthcare system integration not addressed'
            );
        }

        // Check for Google Maps Taiwan configuration
        if (content.includes('Google') && content.includes('Maps')) {
            if (!content.includes('regionCode') && !content.includes('languageCode')) {
                this.validationResults.technicalIssues.push(
                    'Google Maps Taiwan localization parameters not specified'
                );
            }
        }
    }

    async validatePDPACompliance(design) {
        console.log('🔒 Validating PDPA compliance...');

        const content = design.content.toLowerCase();

        // Check for PDPA mention
        if (!content.includes('pdpa') && !content.includes('personal data protection')) {
            this.validationResults.technicalIssues.push(
                'PDPA (Personal Data Protection Act) compliance not addressed'
            );
        }

        // Check for data minimization
        if (!content.includes('minimize') && !content.includes('minimal') && !content.includes('necessary')) {
            this.validationResults.technicalIssues.push(
                'Data minimization principles not specified'
            );
        }

        // Check for audit logging without PII
        if (content.includes('log') && !content.includes('mask') && !content.includes('anonymize')) {
            this.validationResults.technicalIssues.push(
                'Audit logging may expose PII - masking/anonymization not specified'
            );
        }

        // Check for user consent
        if (!content.includes('consent') && !content.includes('agreement')) {
            this.validationResults.technicalIssues.push(
                'User consent and data collection agreement not addressed'
            );
        }
    }

    async validateDocumentationQuality(design) {
        console.log('📚 Validating documentation quality...');

        // Check for sufficient Mermaid diagrams
        if (design.diagrams.length < 2) {
            this.validationResults.documentationIssues.push(
                'Insufficient architectural diagrams - recommend at least 2 different diagram types'
            );
        }

        // Check for code examples
        const codeBlocks = (design.content.match(/```/g) || []).length / 2;
        if (codeBlocks < 2) {
            this.validationResults.documentationIssues.push(
                'Missing code examples - recommend including implementation examples'
            );
        }

        // Check for API specifications
        if (!design.content.includes('endpoint') && !design.content.includes('route') && !design.content.includes('path')) {
            this.validationResults.documentationIssues.push(
                'API endpoint specifications missing or unclear'
            );
        }

        // Check for data model definitions
        if (!design.content.includes('model') && !design.content.includes('schema') && !design.content.includes('structure')) {
            this.validationResults.documentationIssues.push(
                'Data model definitions missing or unclear'
            );
        }
    }

    async validateTDDReadiness(design) {
        console.log('🧪 Validating TDD readiness...');

        const content = design.content.toLowerCase();

        // Check for testing strategy
        if (!content.includes('test') && !content.includes('tdd') && !content.includes('pytest')) {
            this.validationResults.technicalIssues.push(
                'Testing strategy and TDD approach not specified'
            );
        }

        // Check for testable components
        if (!content.includes('unit') && !content.includes('integration') && !content.includes('e2e')) {
            this.validationResults.technicalIssues.push(
                'Test types (unit, integration, e2e) not defined'
            );
        }

        // Check for mock/stub strategies
        if (content.includes('external') || content.includes('api')) {
            if (!content.includes('mock') && !content.includes('stub') && !content.includes('respx')) {
                this.validationResults.technicalIssues.push(
                    'External API mocking strategy for tests not specified'
                );
            }
        }
    }

    calculateOverallRating() {
        const totalIssues = this.validationResults.templateCompliance.length +
                          this.validationResults.requirementsCoverage.length +
                          this.validationResults.requirementsAlignment.length +
                          this.validationResults.technicalIssues.length +
                          this.validationResults.integrationGaps.length +
                          this.validationResults.documentationIssues.length;

        const severityScore = this.calculateSeverityScore();

        if (totalIssues === 0) {
            this.validationResults.overall = 'PASS';
        } else if (totalIssues <= 3 && severityScore < 50) {
            this.validationResults.overall = 'NEEDS_IMPROVEMENT';
        } else {
            this.validationResults.overall = 'MAJOR_ISSUES';
        }

        // Add improvement suggestions based on issues found
        this.generateImprovementSuggestions();
    }

    calculateSeverityScore() {
        let score = 0;

        // Template compliance issues are high severity
        score += this.validationResults.templateCompliance.length * 20;

        // Requirements coverage is critical
        score += this.validationResults.requirementsCoverage.length * 25;

        // Technical issues vary in severity
        score += this.validationResults.technicalIssues.length * 15;

        // Documentation issues are medium severity
        score += this.validationResults.documentationIssues.length * 10;

        return score;
    }

    generateImprovementSuggestions() {
        if (this.validationResults.templateCompliance.length > 0) {
            this.validationResults.improvementSuggestions.push(
                'Review design-template.md and ensure all required sections are included with proper formatting'
            );
        }

        if (this.validationResults.requirementsCoverage.length > 0) {
            this.validationResults.improvementSuggestions.push(
                'Map each requirement from requirements.md to specific design solutions and document the mapping'
            );
        }

        if (this.validationResults.technicalIssues.length > 3) {
            this.validationResults.improvementSuggestions.push(
                'Conduct technical architecture review with focus on FastAPI patterns, security, and Taiwan healthcare integration'
            );
        }

        if (this.validationResults.documentationIssues.length > 0) {
            this.validationResults.improvementSuggestions.push(
                'Add more architectural diagrams and code examples to clarify implementation approach'
            );
        }
    }

    async storeValidationResults(designPath) {
        const timestamp = new Date().toISOString();
        const featureName = path.basename(designPath, '.md');
        const memoryKey = `spec/validation/${featureName}/${timestamp}`;

        try {
            // Store in project memory (simulated as file for now)
            const resultsPath = path.join(
                path.dirname(designPath),
                '..',
                'validation',
                'reports',
                `${featureName}-validation-${Date.now()}.json`
            );

            await fs.writeFile(resultsPath, JSON.stringify({
                timestamp,
                designPath,
                memoryKey,
                results: this.validationResults
            }, null, 2));

            console.log(`💾 Validation results stored: ${resultsPath}`);
            console.log(`🔑 Memory key: ${memoryKey}`);
        } catch (error) {
            console.warn('⚠️ Could not store validation results:', error.message);
        }
    }

    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            rating: this.validationResults.overall,
            summary: this.generateSummary(),
            details: this.validationResults
        };

        console.log('\n📊 VALIDATION REPORT');
        console.log('='.repeat(50));
        console.log(`Overall Rating: ${this.validationResults.overall}`);
        console.log(`Template Compliance Issues: ${this.validationResults.templateCompliance.length}`);
        console.log(`Requirements Coverage Issues: ${this.validationResults.requirementsCoverage.length}`);
        console.log(`Technical Issues: ${this.validationResults.technicalIssues.length}`);
        console.log(`Documentation Issues: ${this.validationResults.documentationIssues.length}`);
        console.log(`Strengths Identified: ${this.validationResults.strengths.length}`);
        console.log('='.repeat(50));

        return report;
    }

    generateSummary() {
        const totalIssues = Object.values(this.validationResults)
            .filter(Array.isArray)
            .reduce((sum, arr) => sum + arr.length, 0) - this.validationResults.strengths.length;

        if (this.validationResults.overall === 'PASS') {
            return 'Design validation successful. Document is technically sound and ready for implementation.';
        } else if (this.validationResults.overall === 'NEEDS_IMPROVEMENT') {
            return `Design has ${totalIssues} minor issues that should be addressed before implementation.`;
        } else {
            return `Design has ${totalIssues} significant issues requiring attention before proceeding.`;
        }
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);

    if (args.length < 1) {
        console.log('Usage: node spec-design-validator.js <design-path> [requirements-path] [template-path]');
        process.exit(1);
    }

    const validator = new SpecDesignValidator();
    validator.validateDesign(args[0], args[1], args[2])
        .then(report => {
            console.log('\n✅ Validation completed');
            process.exit(report.rating === 'PASS' ? 0 : 1);
        })
        .catch(error => {
            console.error('❌ Validation failed:', error);
            process.exit(1);
        });
}

module.exports = SpecDesignValidator;