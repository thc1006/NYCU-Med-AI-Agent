#!/usr/bin/env node

/**
 * PDPA Privacy Protection Validator
 *
 * Validates design documents for Taiwan Personal Data Protection Act (PDPA) compliance:
 * - Data minimization principles
 * - User consent mechanisms
 * - Data processing limitations
 * - Audit trail requirements
 * - User rights implementation
 * - Medical data special protections
 */

const fs = require('fs').promises;
const path = require('path');

class PDPAPrivacyValidator {
    constructor() {
        this.validationResults = {
            dataMinimization: [],
            userConsent: [],
            dataProcessing: [],
            auditCompliance: [],
            userRights: [],
            medicalDataProtection: [],
            technicalSafeguards: [],
            strengths: []
        };

        this.pdpaRequirements = {
            dataMinimization: {
                principles: ['最小必要', 'minimal', 'necessary', 'purpose limitation'],
                prohibited: ['collect all', 'store everything', 'unlimited data', 'comprehensive profile']
            },
            userConsent: {
                required: ['explicit consent', 'informed consent', 'opt-in', '明確同意', '知情同意'],
                mechanisms: ['checkbox', 'agreement', 'confirmation', 'acknowledge']
            },
            medicalDataProtections: {
                sensitiveCategories: ['symptom', 'medical history', 'health condition', 'disease', 'medication'],
                extraProtections: ['encryption', 'anonymization', 'pseudonymization', 'access control']
            },
            userRights: {
                required: ['access', 'correction', 'deletion', 'portability', 'objection'],
                taiwanese: ['查詢', '更正', '刪除', '停止處理', '資料可攜性']
            }
        };

        this.riskPatterns = {
            highRisk: [
                'store.*symptom.*text',
                'log.*medical.*data',
                'permanent.*storage',
                'unlimited.*retention',
                'no.*deletion',
                'share.*with.*third.*party'
            ],
            mediumRisk: [
                'session.*storage',
                'temporary.*cache',
                'analytics.*data',
                'usage.*patterns',
                'ip.*address.*storage'
            ],
            dataExposure: [
                'plain.*text.*log',
                'unencrypted.*storage',
                'clear.*text.*transmission',
                'no.*masking',
                'visible.*in.*log'
            ]
        };
    }

    async validateDocument(designPath) {
        try {
            console.log(`🔒 Validating PDPA compliance for: ${path.basename(designPath)}`);

            const design = await this.loadDocument(designPath);

            // Run all PDPA compliance validations
            await this.validateDataMinimization(design);
            await this.validateUserConsent(design);
            await this.validateDataProcessing(design);
            await this.validateAuditCompliance(design);
            await this.validateUserRights(design);
            await this.validateMedicalDataProtection(design);
            await this.validateTechnicalSafeguards(design);

            // Generate comprehensive PDPA compliance report
            return this.generatePDPAReport();

        } catch (error) {
            console.error('❌ PDPA validation failed:', error.message);
            return {
                overall: 'PDPA_VALIDATION_ERROR',
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
            lines: content.split('\n')
        };
    }

    async validateDataMinimization(design) {
        console.log('📉 Validating data minimization principles...');

        const content = design.contentLower;

        // Check for data minimization principle mention
        const hasMinimizationPrinciple = this.pdpaRequirements.dataMinimization.principles.some(
            principle => content.includes(principle)
        );

        if (!hasMinimizationPrinciple) {
            this.validationResults.dataMinimization.push(
                'PDPA data minimization principle not explicitly addressed'
            );
        }

        // Check for prohibited data collection patterns
        const prohibitedPatterns = this.pdpaRequirements.dataMinimization.prohibited.filter(
            pattern => content.includes(pattern)
        );

        if (prohibitedPatterns.length > 0) {
            this.validationResults.dataMinimization.push(
                `Potential PDPA violation - excessive data collection: ${prohibitedPatterns.join(', ')}`
            );
        }

        // Check for purpose limitation
        if (!content.includes('purpose') && !content.includes('目的')) {
            this.validationResults.dataMinimization.push(
                'Purpose limitation principle not specified for data collection'
            );
        }

        // Check for data retention periods
        if (!content.includes('retention') && !content.includes('保存期限') && !content.includes('delete')) {
            this.validationResults.dataMinimization.push(
                'Data retention periods not specified - PDPA requires defined retention limits'
            );
        }

        // Check for automatic deletion mechanisms
        if (content.includes('automatic.*delete') || content.includes('自動刪除')) {
            this.validationResults.strengths.push(
                'Automatic data deletion mechanisms support PDPA compliance'
            );
        }

        // Validate specific medical data minimization
        if (content.includes('symptom')) {
            if (!content.includes('hash') && !content.includes('anonymize') && !content.includes('不儲存')) {
                this.validationResults.dataMinimization.push(
                    'Symptom data processing should be minimized - consider hashing or not storing raw text'
                );
            }
        }
    }

    async validateUserConsent(design) {
        console.log('✋ Validating user consent mechanisms...');

        const content = design.contentLower;

        // Check for explicit consent requirements
        const hasConsentMechanism = this.pdpaRequirements.userConsent.required.some(
            consent => content.includes(consent)
        );

        if (!hasConsentMechanism) {
            this.validationResults.userConsent.push(
                'Explicit user consent mechanism not specified - required for PDPA compliance'
            );
        }

        // Check for informed consent (user understanding)
        if (!content.includes('informed') && !content.includes('知情') && !content.includes('說明')) {
            this.validationResults.userConsent.push(
                'Informed consent process not described - users must understand data processing'
            );
        }

        // Check for consent withdrawal mechanism
        if (!content.includes('withdraw') && !content.includes('撤回') && !content.includes('取消同意')) {
            this.validationResults.userConsent.push(
                'Consent withdrawal mechanism not specified - PDPA requires ability to withdraw consent'
            );
        }

        // Check for granular consent options
        if (content.includes('granular') || content.includes('specific') || content.includes('分別同意')) {
            this.validationResults.strengths.push(
                'Granular consent options support PDPA user choice requirements'
            );
        }

        // Validate consent for sensitive medical data
        if (content.includes('medical') || content.includes('health') || content.includes('symptom')) {
            if (!content.includes('special.*consent') && !content.includes('additional.*consent')) {
                this.validationResults.userConsent.push(
                    'Medical/health data requires enhanced consent mechanisms under PDPA'
                );
            }
        }

        // Check for consent documentation
        if (content.includes('consent.*log') || content.includes('audit.*consent')) {
            this.validationResults.strengths.push(
                'Consent documentation and audit trail enhances PDPA compliance'
            );
        }
    }

    async validateDataProcessing(design) {
        console.log('⚙️ Validating data processing limitations...');

        const content = design.contentLower;

        // Check for lawful basis specification
        if (!content.includes('lawful.*basis') && !content.includes('法律依據') && !content.includes('合法性基礎')) {
            this.validationResults.dataProcessing.push(
                'Lawful basis for data processing not specified - required under PDPA'
            );
        }

        // Check for processing transparency
        if (!content.includes('transparent') && !content.includes('透明') && !content.includes('公開')) {
            this.validationResults.dataProcessing.push(
                'Data processing transparency requirements not addressed'
            );
        }

        // Check for third-party data sharing limitations
        if (content.includes('share') || content.includes('third.*party') || content.includes('第三方')) {
            if (!content.includes('user.*consent') && !content.includes('使用者同意')) {
                this.validationResults.dataProcessing.push(
                    'Third-party data sharing requires explicit user consent under PDPA'
                );
            }
        }

        // Check for cross-border data transfer restrictions
        if (content.includes('cross.*border') || content.includes('international') || content.includes('境外')) {
            if (!content.includes('adequacy') && !content.includes('safeguards') && !content.includes('保護措施')) {
                this.validationResults.dataProcessing.push(
                    'Cross-border data transfers require adequate protection measures under PDPA'
                );
            }
        }

        // Validate automated decision-making disclosure
        if (content.includes('ai') || content.includes('algorithm') || content.includes('automated')) {
            if (!content.includes('automated.*decision') && !content.includes('人工智慧決策')) {
                this.validationResults.dataProcessing.push(
                    'Automated decision-making (AI) should be disclosed to users under PDPA'
                );
            }
        }

        // Check for data accuracy measures
        if (content.includes('accuracy') || content.includes('correct') || content.includes('準確性')) {
            this.validationResults.strengths.push(
                'Data accuracy measures support PDPA data quality requirements'
            );
        }
    }

    async validateAuditCompliance(design) {
        console.log('📋 Validating audit trail compliance...');

        const content = design.contentLower;

        // Check for audit logging without PII
        if (content.includes('audit') || content.includes('log')) {
            // Look for PII protection in logging
            if (!content.includes('mask') && !content.includes('anonymize') && !content.includes('遮罩')) {
                this.validationResults.auditCompliance.push(
                    'Audit logging must protect PII - implement masking or anonymization'
                );
            } else {
                this.validationResults.strengths.push(
                    'Audit logging includes PII protection measures'
                );
            }
        }

        // Check for activity tracking compliance
        if (!content.includes('audit') && !content.includes('activity.*log') && !content.includes('稽核')) {
            this.validationResults.auditCompliance.push(
                'Audit trail requirements not addressed - PDPA requires activity tracking'
            );
        }

        // Validate log retention periods
        if (content.includes('log.*retention') || content.includes('紀錄保存')) {
            this.validationResults.strengths.push(
                'Log retention periods specified for PDPA compliance'
            );
        }

        // Check for security incident logging
        if (content.includes('security.*incident') || content.includes('breach.*log')) {
            this.validationResults.strengths.push(
                'Security incident logging supports PDPA breach notification requirements'
            );
        }

        // Validate access logging
        if (content.includes('access.*log') || content.includes('存取紀錄')) {
            this.validationResults.strengths.push(
                'Data access logging enhances PDPA accountability'
            );
        }

        // Check for audit trail integrity
        if (content.includes('tamper.*proof') || content.includes('integrity') || content.includes('完整性')) {
            this.validationResults.strengths.push(
                'Audit trail integrity measures support PDPA compliance'
            );
        }
    }

    async validateUserRights(design) {
        console.log('👤 Validating user rights implementation...');

        const content = design.contentLower;

        // Check for data subject access rights
        const accessRights = ['access', 'view', 'retrieve', '查詢', '檢視'];
        const hasAccessRights = accessRights.some(right => content.includes(right));

        if (!hasAccessRights) {
            this.validationResults.userRights.push(
                'Data subject access rights not implemented - PDPA requires user data access'
            );
        }

        // Check for data correction rights
        const correctionRights = ['correct', 'update', 'modify', '更正', '修改'];
        const hasCorrectionRights = correctionRights.some(right => content.includes(right));

        if (!hasCorrectionRights) {
            this.validationResults.userRights.push(
                'Data correction rights not implemented - PDPA requires error correction capability'
            );
        }

        // Check for data deletion rights (right to be forgotten)
        const deletionRights = ['delete', 'remove', 'forget', '刪除', '遺忘權'];
        const hasDeletionRights = deletionRights.some(right => content.includes(right));

        if (!hasDeletionRights) {
            this.validationResults.userRights.push(
                'Data deletion rights not implemented - PDPA requires right to erasure'
            );
        }

        // Check for data portability
        if (content.includes('portability') || content.includes('export') || content.includes('可攜性')) {
            this.validationResults.strengths.push(
                'Data portability rights support PDPA user control requirements'
            );
        }

        // Check for processing objection rights
        if (content.includes('object') || content.includes('opt.*out') || content.includes('反對處理')) {
            this.validationResults.strengths.push(
                'Right to object to processing supports PDPA user control'
            );
        }

        // Validate user control interface
        if (content.includes('user.*dashboard') || content.includes('privacy.*settings') || content.includes('隱私設定')) {
            this.validationResults.strengths.push(
                'User privacy control interface enhances PDPA rights implementation'
            );
        }

        // Check for rights request handling
        if (content.includes('request.*handling') || content.includes('權利請求處理')) {
            this.validationResults.strengths.push(
                'User rights request handling process supports PDPA compliance'
            );
        }
    }

    async validateMedicalDataProtection(design) {
        console.log('🏥 Validating medical data special protections...');

        const content = design.contentLower;

        // Check for medical data identification
        const hasMedicalData = this.pdpaRequirements.medicalDataProtections.sensitiveCategories.some(
            category => content.includes(category)
        );

        if (hasMedicalData) {
            // Check for enhanced protections
            const hasProtections = this.pdpaRequirements.medicalDataProtections.extraProtections.some(
                protection => content.includes(protection)
            );

            if (!hasProtections) {
                this.validationResults.medicalDataProtection.push(
                    'Medical data requires enhanced protection measures (encryption, anonymization, etc.)'
                );
            }

            // Check for medical professional access controls
            if (!content.includes('medical.*professional') && !content.includes('healthcare.*provider')) {
                this.validationResults.medicalDataProtection.push(
                    'Medical data access should be restricted to qualified healthcare professionals'
                );
            }

            // Check for medical data encryption
            if (!content.includes('encrypt') && !content.includes('加密')) {
                this.validationResults.medicalDataProtection.push(
                    'Medical data encryption not specified - required for sensitive health data'
                );
            }

            // Check for medical data anonymization
            if (content.includes('anonymous') || content.includes('匿名')) {
                this.validationResults.strengths.push(
                    'Medical data anonymization supports PDPA sensitive data protection'
                );
            }

            // Check for medical data segregation
            if (content.includes('segregat') || content.includes('isolat') || content.includes('分離')) {
                this.validationResults.strengths.push(
                    'Medical data segregation enhances PDPA sensitive data protection'
                );
            }
        }

        // Check for health data consent mechanisms
        if (content.includes('health.*consent') || content.includes('medical.*consent')) {
            this.validationResults.strengths.push(
                'Specific health data consent mechanisms support PDPA sensitive data requirements'
            );
        }

        // Validate medical confidentiality measures
        if (content.includes('confidential') || content.includes('機密')) {
            this.validationResults.strengths.push(
                'Medical confidentiality measures support PDPA sensitive data protection'
            );
        }
    }

    async validateTechnicalSafeguards(design) {
        console.log('🛡️ Validating technical safeguards...');

        const content = design.contentLower;

        // Check for encryption implementation
        if (!content.includes('encrypt') && !content.includes('加密')) {
            this.validationResults.technicalSafeguards.push(
                'Encryption not specified - PDPA requires appropriate technical measures'
            );
        }

        // Check for access controls
        if (!content.includes('access.*control') && !content.includes('auth') && !content.includes('存取控制')) {
            this.validationResults.technicalSafeguards.push(
                'Access controls not specified - required for PDPA data protection'
            );
        }

        // Check for data breach detection
        if (content.includes('breach.*detection') || content.includes('intrusion') || content.includes('異常偵測')) {
            this.validationResults.strengths.push(
                'Data breach detection supports PDPA incident response requirements'
            );
        }

        // Check for backup and recovery security
        if (content.includes('backup') && content.includes('secur')) {
            this.validationResults.strengths.push(
                'Secure backup and recovery supports PDPA data protection'
            );
        }

        // Validate network security measures
        if (content.includes('firewall') || content.includes('network.*secur') || content.includes('防火牆')) {
            this.validationResults.strengths.push(
                'Network security measures support PDPA technical safeguards'
            );
        }

        // Check for vulnerability management
        if (content.includes('vulnerabil') || content.includes('patch') || content.includes('漏洞管理')) {
            this.validationResults.strengths.push(
                'Vulnerability management supports PDPA security requirements'
            );
        }

        // Check for secure development practices
        if (content.includes('secure.*development') || content.includes('security.*by.*design')) {
            this.validationResults.strengths.push(
                'Security by design approach enhances PDPA compliance'
            );
        }
    }

    generatePDPAReport() {
        const categories = Object.keys(this.validationResults).filter(key => key !== 'strengths');
        const totalIssues = categories.reduce((sum, key) => sum + this.validationResults[key].length, 0);
        const totalStrengths = this.validationResults.strengths.length;

        let overallRating;
        let complianceLevel;

        if (totalIssues === 0) {
            overallRating = 'PDPA_FULLY_COMPLIANT';
            complianceLevel = 100;
        } else if (totalIssues <= 2) {
            overallRating = 'PDPA_MOSTLY_COMPLIANT';
            complianceLevel = 85;
        } else if (totalIssues <= 5) {
            overallRating = 'PDPA_NEEDS_IMPROVEMENT';
            complianceLevel = 65;
        } else {
            overallRating = 'PDPA_MAJOR_ISSUES';
            complianceLevel = 35;
        }

        const report = {
            timestamp: new Date().toISOString(),
            overall: overallRating,
            complianceLevel,
            summary: this.generateComplianceSummary(overallRating, totalIssues, totalStrengths),
            breakdown: {
                dataMinimization: this.validationResults.dataMinimization,
                userConsent: this.validationResults.userConsent,
                dataProcessing: this.validationResults.dataProcessing,
                auditCompliance: this.validationResults.auditCompliance,
                userRights: this.validationResults.userRights,
                medicalDataProtection: this.validationResults.medicalDataProtection,
                technicalSafeguards: this.validationResults.technicalSafeguards,
                strengths: this.validationResults.strengths
            },
            riskAssessment: this.generateRiskAssessment(),
            recommendations: this.generatePDPARecommendations(),
            complianceMatrix: this.generateComplianceMatrix()
        };

        this.printPDPAReport(report);
        return report;
    }

    generateComplianceSummary(rating, issues, strengths) {
        switch (rating) {
            case 'PDPA_FULLY_COMPLIANT':
                return `🔒 Full PDPA compliance achieved with ${strengths} privacy protection strengths`;
            case 'PDPA_MOSTLY_COMPLIANT':
                return `🔒 Strong PDPA compliance with ${issues} minor issues and ${strengths} strengths`;
            case 'PDPA_NEEDS_IMPROVEMENT':
                return `🔒 PDPA compliance needs improvement: ${issues} issues to address`;
            case 'PDPA_MAJOR_ISSUES':
                return `🔒 Major PDPA compliance issues: ${issues} critical privacy concerns`;
            default:
                return 'PDPA compliance validation completed';
        }
    }

    generateRiskAssessment() {
        const risks = {
            high: [],
            medium: [],
            low: []
        };

        if (this.validationResults.medicalDataProtection.length > 0) {
            risks.high.push('Medical data protection deficiencies');
        }

        if (this.validationResults.userConsent.length > 0) {
            risks.high.push('User consent mechanism inadequacies');
        }

        if (this.validationResults.dataMinimization.length > 0) {
            risks.medium.push('Data minimization principle violations');
        }

        if (this.validationResults.technicalSafeguards.length > 0) {
            risks.medium.push('Technical safeguard gaps');
        }

        if (this.validationResults.auditCompliance.length > 0) {
            risks.low.push('Audit trail compliance issues');
        }

        return risks;
    }

    generatePDPARecommendations() {
        const recommendations = [];

        if (this.validationResults.dataMinimization.length > 0) {
            recommendations.push({
                category: 'Data Minimization',
                priority: 'High',
                action: 'Implement explicit data minimization principles and purpose limitation',
                timeline: 'Before implementation'
            });
        }

        if (this.validationResults.userConsent.length > 0) {
            recommendations.push({
                category: 'User Consent',
                priority: 'Critical',
                action: 'Develop comprehensive user consent mechanisms with withdrawal options',
                timeline: 'Before user testing'
            });
        }

        if (this.validationResults.medicalDataProtection.length > 0) {
            recommendations.push({
                category: 'Medical Data',
                priority: 'Critical',
                action: 'Implement enhanced protection measures for sensitive health data',
                timeline: 'Before implementation'
            });
        }

        if (this.validationResults.userRights.length > 0) {
            recommendations.push({
                category: 'User Rights',
                priority: 'High',
                action: 'Implement data subject rights (access, correction, deletion)',
                timeline: 'Before production'
            });
        }

        if (this.validationResults.technicalSafeguards.length > 0) {
            recommendations.push({
                category: 'Technical Security',
                priority: 'Medium',
                action: 'Strengthen technical safeguards and security measures',
                timeline: 'During development'
            });
        }

        return recommendations;
    }

    generateComplianceMatrix() {
        return {
            dataMinimization: this.validationResults.dataMinimization.length === 0,
            userConsent: this.validationResults.userConsent.length === 0,
            dataProcessing: this.validationResults.dataProcessing.length === 0,
            auditCompliance: this.validationResults.auditCompliance.length === 0,
            userRights: this.validationResults.userRights.length === 0,
            medicalDataProtection: this.validationResults.medicalDataProtection.length === 0,
            technicalSafeguards: this.validationResults.technicalSafeguards.length === 0
        };
    }

    printPDPAReport(report) {
        console.log('\n🔒 PDPA PRIVACY COMPLIANCE VALIDATION REPORT');
        console.log('='.repeat(60));
        console.log(`Overall Rating: ${report.overall}`);
        console.log(`Compliance Level: ${report.complianceLevel}%`);
        console.log(`Summary: ${report.summary}`);
        console.log('');

        console.log('📊 Compliance Matrix:');
        Object.entries(report.complianceMatrix).forEach(([area, compliant]) => {
            const status = compliant ? '✅' : '❌';
            const displayName = area.replace(/([A-Z])/g, ' $1').toLowerCase();
            console.log(`  ${status} ${displayName.charAt(0).toUpperCase() + displayName.slice(1)}`);
        });

        console.log('');
        console.log('⚠️  PDPA Compliance Issues:');
        Object.entries(report.breakdown).forEach(([category, issues]) => {
            if (category !== 'strengths' && issues.length > 0) {
                const displayName = category.replace(/([A-Z])/g, ' $1').toLowerCase();
                console.log(`  ${displayName}: ${issues.length} issues`);
                issues.forEach(issue => console.log(`    - ${issue}`));
            }
        });

        console.log('');
        console.log('🛡️ Privacy Protection Strengths:');
        report.breakdown.strengths.forEach(strength => {
            console.log(`  + ${strength}`);
        });

        console.log('');
        console.log('🚨 Risk Assessment:');
        Object.entries(report.riskAssessment).forEach(([level, risks]) => {
            if (risks.length > 0) {
                console.log(`  ${level.toUpperCase()} RISK:`);
                risks.forEach(risk => console.log(`    ⚠️  ${risk}`));
            }
        });

        if (report.recommendations.length > 0) {
            console.log('');
            console.log('📋 PDPA Compliance Recommendations:');
            report.recommendations.forEach(rec => {
                console.log(`  [${rec.priority}] ${rec.category}: ${rec.action}`);
                console.log(`    Timeline: ${rec.timeline}`);
            });
        }

        console.log('='.repeat(60));
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);

    if (args.length < 1) {
        console.log('Usage: node pdpa-privacy-validator.js <design-path>');
        console.log('');
        console.log('Validates design documents for Taiwan PDPA compliance:');
        console.log('  - Data minimization and purpose limitation');
        console.log('  - User consent mechanisms');
        console.log('  - Data processing transparency');
        console.log('  - Audit compliance without PII exposure');
        console.log('  - User rights implementation');
        console.log('  - Medical data special protections');
        console.log('  - Technical security safeguards');
        process.exit(1);
    }

    const validator = new PDPAPrivacyValidator();
    validator.validateDocument(args[0])
        .then(report => {
            const success = report.overall.includes('COMPLIANT');
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('❌ PDPA validation failed:', error);
            process.exit(1);
        });
}

module.exports = PDPAPrivacyValidator;