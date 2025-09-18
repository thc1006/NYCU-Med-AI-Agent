#!/usr/bin/env node

/**
 * Taiwan Localization Compliance Validator
 *
 * Validates design documents for Taiwan-specific requirements:
 * - Traditional Chinese (zh-TW) compliance
 * - Taiwan emergency protocols
 * - Healthcare system integration
 * - Regional service configuration
 * - Cultural sensitivity
 */

const fs = require('fs').promises;
const path = require('path');

class TaiwanLocalizationValidator {
    constructor() {
        this.validationResults = {
            languageCompliance: [],
            emergencyProtocols: [],
            healthcareIntegration: [],
            serviceConfiguration: [],
            culturalSensitivity: [],
            strengths: []
        };

        this.taiwanRequirements = {
            emergencyNumbers: {
                '119': '消防及救護車',
                '110': '警察局',
                '112': '行動電話國際緊急號碼',
                '113': '婦幼保護專線',
                '165': '反詐騙諮詢專線'
            },
            languageCodes: ['zh-TW', 'zh_TW'],
            regionCodes: ['TW', 'Taiwan'],
            healthcareTerms: ['健保', '健保署', 'NHI', 'MOHW', '衛生福利部', '醫療院所'],
            googleServicesParams: {
                places: ['languageCode=zh-TW', 'regionCode=TW'],
                geocoding: ['language=zh-TW', 'region=tw'],
                maps: ['hl=zh-TW', 'region=TW']
            }
        };

        this.traditionalChinesePatterns = {
            required: ['台灣', '醫療', '健康', '醫院', '診所', '緊急', '症狀'],
            forbidden: ['台湾', '医疗', '健康', '医院', '诊所', '紧急', '症状'] // Simplified Chinese
        };
    }

    async validateDocument(designPath) {
        try {
            console.log(`🇹🇼 Validating Taiwan localization for: ${path.basename(designPath)}`);

            const design = await this.loadDocument(designPath);

            // Run all Taiwan-specific validations
            await this.validateLanguageCompliance(design);
            await this.validateEmergencyProtocols(design);
            await this.validateHealthcareIntegration(design);
            await this.validateServiceConfiguration(design);
            await this.validateCulturalSensitivity(design);

            // Generate comprehensive report
            return this.generateValidationReport();

        } catch (error) {
            console.error('❌ Taiwan localization validation failed:', error.message);
            return {
                overall: 'ERROR',
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
            contentLower: content.toLowerCase()
        };
    }

    async validateLanguageCompliance(design) {
        console.log('📝 Validating Traditional Chinese compliance...');

        const content = design.content;

        // Check for zh-TW specification
        const hasLanguageCode = this.taiwanRequirements.languageCodes.some(code =>
            content.includes(code)
        );

        if (!hasLanguageCode) {
            this.validationResults.languageCompliance.push(
                'Missing zh-TW language code specification for Traditional Chinese support'
            );
        }

        // Check for simplified Chinese characters (should not be present)
        const forbiddenChars = this.taiwanRequirements.traditionalChinesePatterns.forbidden.filter(
            char => content.includes(char)
        );

        if (forbiddenChars.length > 0) {
            this.validationResults.languageCompliance.push(
                `Simplified Chinese characters detected: ${forbiddenChars.join(', ')} - should use Traditional Chinese`
            );
        }

        // Check for proper Traditional Chinese medical terminology
        const requiredTerms = this.taiwanRequirements.traditionalChinesePatterns.required;
        const missingTerms = requiredTerms.filter(term => !content.includes(term));

        if (missingTerms.length > requiredTerms.length * 0.5) {
            this.validationResults.languageCompliance.push(
                'Limited Traditional Chinese medical terminology - consider adding more Taiwan-specific terms'
            );
        }

        // Check for Unicode normalization considerations
        if (content.includes('正規化') || content.includes('normalize')) {
            this.validationResults.strengths.push(
                'Document addresses Unicode normalization for Traditional Chinese text processing'
            );
        }

        if (this.validationResults.languageCompliance.length === 0) {
            this.validationResults.strengths.push(
                'Excellent Traditional Chinese (zh-TW) language compliance'
            );
        }
    }

    async validateEmergencyProtocols(design) {
        console.log('🚨 Validating Taiwan emergency protocols...');

        const content = design.content;

        // Check for all required emergency numbers
        const missingNumbers = Object.keys(this.taiwanRequirements.emergencyNumbers).filter(
            number => !content.includes(number)
        );

        if (missingNumbers.length > 0) {
            this.validationResults.emergencyProtocols.push(
                `Missing Taiwan emergency numbers: ${missingNumbers.join(', ')}`
            );
        }

        // Check for 119 prominence (most important for medical emergencies)
        const emergencyTexts = content.split('\n').filter(line =>
            line.includes('119') || line.includes('緊急')
        );

        if (emergencyTexts.length < 2) {
            this.validationResults.emergencyProtocols.push(
                '119 emergency number should be prominently featured for medical emergencies'
            );
        }

        // Check for 112 GSM emergency explanation
        if (content.includes('112')) {
            if (!content.includes('國際緊急') && !content.includes('無卡')) {
                this.validationResults.emergencyProtocols.push(
                    '112 should be explained as GSM international emergency number (card-free capable)'
                );
            } else {
                this.validationResults.strengths.push(
                    'Proper explanation of 112 GSM emergency capabilities'
                );
            }
        }

        // Check for emergency escalation workflow
        if (!content.includes('escalation') && !content.includes('升級') && !content.includes('轉介')) {
            this.validationResults.emergencyProtocols.push(
                'Emergency escalation workflow not clearly defined'
            );
        }

        // Validate emergency response timing
        const timePatterns = ['<2', '2秒', '立即', 'immediate'];
        const hasTimingRequirements = timePatterns.some(pattern => content.includes(pattern));

        if (!hasTimingRequirements) {
            this.validationResults.emergencyProtocols.push(
                'Emergency response time requirements not specified (should be <2 seconds for critical symptoms)'
            );
        }
    }

    async validateHealthcareIntegration(design) {
        console.log('🏥 Validating Taiwan healthcare system integration...');

        const content = design.contentLower;

        // Check for Taiwan healthcare system references
        const healthcareTermsFound = this.taiwanRequirements.healthcareTerms.filter(
            term => content.includes(term.toLowerCase())
        );

        if (healthcareTermsFound.length === 0) {
            this.validationResults.healthcareIntegration.push(
                'No references to Taiwan healthcare system (健保署, MOHW, NHI)'
            );
        } else if (healthcareTermsFound.length < 2) {
            this.validationResults.healthcareIntegration.push(
                'Limited Taiwan healthcare system integration - consider more comprehensive references'
            );
        }

        // Check for hospital classification understanding
        const hospitalTypes = ['醫學中心', '區域醫院', '地區醫院', '診所'];
        const hospitalTypesFound = hospitalTypes.filter(type => content.includes(type));

        if (hospitalTypesFound.length === 0) {
            this.validationResults.healthcareIntegration.push(
                'Taiwan hospital classification system not addressed (醫學中心, 區域醫院, 地區醫院, 診所)'
            );
        }

        // Check for NHI contractor verification
        if (content.includes('健保') || content.includes('nhi')) {
            if (!content.includes('特約') && !content.includes('contract')) {
                this.validationResults.healthcareIntegration.push(
                    'NHI contracted facility verification not mentioned'
                );
            } else {
                this.validationResults.strengths.push(
                    'NHI contracted facility verification included'
                );
            }
        }

        // Check for MOHW data source references
        if (content.includes('mohw') || content.includes('衛生福利部')) {
            this.validationResults.strengths.push(
                'MOHW (Ministry of Health and Welfare) data sources referenced'
            );
        }

        // Check for Taiwan medical record standards
        if (content.includes('醫療紀錄') || content.includes('medical record')) {
            this.validationResults.strengths.push(
                'Taiwan medical record standards consideration included'
            );
        }
    }

    async validateServiceConfiguration(design) {
        console.log('⚙️ Validating Taiwan service configuration...');

        const content = design.content;

        // Check Google Places API Taiwan configuration
        if (content.includes('Google') && content.includes('Places')) {
            const hasLanguageCode = content.includes('languageCode=zh-TW') ||
                                  content.includes('languageCode="zh-TW"') ||
                                  content.includes("languageCode:'zh-TW'");

            const hasRegionCode = content.includes('regionCode=TW') ||
                                content.includes('regionCode="TW"') ||
                                content.includes("regionCode:'TW'");

            if (!hasLanguageCode) {
                this.validationResults.serviceConfiguration.push(
                    'Google Places API missing languageCode=zh-TW parameter'
                );
            }

            if (!hasRegionCode) {
                this.validationResults.serviceConfiguration.push(
                    'Google Places API missing regionCode=TW parameter'
                );
            }

            if (hasLanguageCode && hasRegionCode) {
                this.validationResults.strengths.push(
                    'Proper Google Places API Taiwan localization parameters'
                );
            }
        }

        // Check Google Geocoding API Taiwan configuration
        if (content.includes('Geocoding')) {
            const hasGeoLanguage = content.includes('language=zh-TW') ||
                                 content.includes('language=zh_TW');

            if (!hasGeoLanguage) {
                this.validationResults.serviceConfiguration.push(
                    'Google Geocoding API missing language=zh-TW parameter'
                );
            } else {
                this.validationResults.strengths.push(
                    'Proper Google Geocoding API Taiwan language configuration'
                );
            }
        }

        // Check for Taiwan region specification
        const hasRegionCode = this.taiwanRequirements.regionCodes.some(code =>
            content.includes(code)
        );

        if (!hasRegionCode) {
            this.validationResults.serviceConfiguration.push(
                'Taiwan region code (TW) not specified for services'
            );
        }

        // Check for Taiwan data residency considerations
        if (content.includes('data') && (content.includes('storage') || content.includes('processing'))) {
            if (!content.includes('Taiwan') && !content.includes('local')) {
                this.validationResults.serviceConfiguration.push(
                    'Taiwan data residency requirements not addressed'
                );
            }
        }

        // Check for Taiwan-specific backup services
        if (content.includes('backup') || content.includes('failover')) {
            if (content.includes('Taiwan') || content.includes('local')) {
                this.validationResults.strengths.push(
                    'Taiwan-based backup and failover services considered'
                );
            }
        }
    }

    async validateCulturalSensitivity(design) {
        console.log('🎭 Validating cultural sensitivity and local practices...');

        const content = design.contentLower;

        // Check for Traditional Chinese Medicine (TCM) considerations
        const tcmTerms = ['中醫', '中藥', '針灸', '推拿', 'tcm', 'traditional chinese medicine'];
        const hasTCMConsideration = tcmTerms.some(term => content.includes(term));

        if (hasTCMConsideration) {
            this.validationResults.strengths.push(
                'Traditional Chinese Medicine (TCM) practices consideration included'
            );
        }

        // Check for Taiwan health beliefs and practices
        const culturalTerms = ['保健', '養生', '食療', '預防醫學'];
        const hasCulturalTerms = culturalTerms.some(term => content.includes(term));

        if (hasCulturalTerms) {
            this.validationResults.strengths.push(
                'Taiwan health and wellness cultural practices acknowledged'
            );
        }

        // Check for family-centered healthcare approach
        if (content.includes('家屬') || content.includes('family') && content.includes('care')) {
            this.validationResults.strengths.push(
                'Family-centered healthcare approach (common in Taiwan) considered'
            );
        }

        // Check for respect for elderly care traditions
        if (content.includes('長者') || content.includes('elderly') || content.includes('老人')) {
            this.validationResults.strengths.push(
                'Elderly care considerations (important in Taiwan culture) included'
            );
        }

        // Check for preventive healthcare emphasis
        if (content.includes('預防') || content.includes('prevention') || content.includes('screening')) {
            this.validationResults.strengths.push(
                'Preventive healthcare emphasis (Taiwan healthcare focus) included'
            );
        }

        // Check for appropriate formal language level
        if (content.includes('您') || content.includes('敬語')) {
            this.validationResults.strengths.push(
                'Appropriate formal Chinese language level for medical context'
            );
        }

        // Validate accessibility for Taiwan demographics
        if (content.includes('accessibility') || content.includes('無障礙')) {
            this.validationResults.strengths.push(
                'Accessibility considerations for Taiwan demographics included'
            );
        }
    }

    generateValidationReport() {
        const totalIssues = Object.keys(this.validationResults)
            .filter(key => key !== 'strengths')
            .reduce((sum, key) => sum + this.validationResults[key].length, 0);

        const totalStrengths = this.validationResults.strengths.length;

        let overallRating;
        if (totalIssues === 0) {
            overallRating = 'EXCELLENT_TAIWAN_COMPLIANCE';
        } else if (totalIssues <= 2) {
            overallRating = 'GOOD_TAIWAN_COMPLIANCE';
        } else if (totalIssues <= 5) {
            overallRating = 'NEEDS_TAIWAN_IMPROVEMENT';
        } else {
            overallRating = 'MAJOR_TAIWAN_ISSUES';
        }

        const report = {
            timestamp: new Date().toISOString(),
            overall: overallRating,
            summary: this.generateSummary(overallRating, totalIssues, totalStrengths),
            breakdown: {
                languageCompliance: this.validationResults.languageCompliance,
                emergencyProtocols: this.validationResults.emergencyProtocols,
                healthcareIntegration: this.validationResults.healthcareIntegration,
                serviceConfiguration: this.validationResults.serviceConfiguration,
                culturalSensitivity: this.validationResults.culturalSensitivity,
                strengths: this.validationResults.strengths
            },
            recommendations: this.generateRecommendations(),
            compliance: {
                language: this.validationResults.languageCompliance.length === 0,
                emergency: this.validationResults.emergencyProtocols.length === 0,
                healthcare: this.validationResults.healthcareIntegration.length === 0,
                services: this.validationResults.serviceConfiguration.length === 0,
                culture: this.validationResults.culturalSensitivity.length === 0
            }
        };

        this.printReport(report);
        return report;
    }

    generateSummary(rating, issues, strengths) {
        switch (rating) {
            case 'EXCELLENT_TAIWAN_COMPLIANCE':
                return `🇹🇼 Excellent Taiwan localization compliance with ${strengths} strengths identified`;
            case 'GOOD_TAIWAN_COMPLIANCE':
                return `🇹🇼 Good Taiwan compliance with ${issues} minor issues and ${strengths} strengths`;
            case 'NEEDS_TAIWAN_IMPROVEMENT':
                return `🇹🇼 Taiwan localization needs improvement: ${issues} issues to address`;
            case 'MAJOR_TAIWAN_ISSUES':
                return `🇹🇼 Major Taiwan localization issues: ${issues} critical problems requiring attention`;
            default:
                return 'Taiwan localization validation completed';
        }
    }

    generateRecommendations() {
        const recommendations = [];

        if (this.validationResults.languageCompliance.length > 0) {
            recommendations.push({
                category: 'Language',
                priority: 'High',
                action: 'Ensure all text uses Traditional Chinese (zh-TW) and avoid Simplified Chinese characters'
            });
        }

        if (this.validationResults.emergencyProtocols.length > 0) {
            recommendations.push({
                category: 'Emergency',
                priority: 'Critical',
                action: 'Include all Taiwan emergency numbers (119, 110, 112, 113, 165) with proper explanations'
            });
        }

        if (this.validationResults.healthcareIntegration.length > 0) {
            recommendations.push({
                category: 'Healthcare',
                priority: 'High',
                action: 'Reference Taiwan healthcare system components (健保署, MOHW, hospital classifications)'
            });
        }

        if (this.validationResults.serviceConfiguration.length > 0) {
            recommendations.push({
                category: 'Services',
                priority: 'Medium',
                action: 'Configure Google Services with proper Taiwan language and region parameters'
            });
        }

        if (this.validationResults.culturalSensitivity.length === 0 && this.validationResults.strengths.length < 3) {
            recommendations.push({
                category: 'Culture',
                priority: 'Low',
                action: 'Consider adding more Taiwan-specific cultural and healthcare practice considerations'
            });
        }

        return recommendations;
    }

    printReport(report) {
        console.log('\n🇹🇼 TAIWAN LOCALIZATION VALIDATION REPORT');
        console.log('='.repeat(55));
        console.log(`Overall Rating: ${report.overall}`);
        console.log(`Summary: ${report.summary}`);
        console.log('');

        console.log('📊 Compliance Status:');
        Object.entries(report.compliance).forEach(([area, compliant]) => {
            const status = compliant ? '✅' : '❌';
            console.log(`  ${status} ${area.charAt(0).toUpperCase() + area.slice(1)}`);
        });

        console.log('');
        console.log('⚠️  Issues Found:');
        Object.entries(report.breakdown).forEach(([category, issues]) => {
            if (category !== 'strengths' && issues.length > 0) {
                console.log(`  ${category}: ${issues.length} issues`);
                issues.forEach(issue => console.log(`    - ${issue}`));
            }
        });

        console.log('');
        console.log('💪 Strengths:');
        report.breakdown.strengths.forEach(strength => {
            console.log(`  + ${strength}`);
        });

        if (report.recommendations.length > 0) {
            console.log('');
            console.log('📋 Recommendations:');
            report.recommendations.forEach(rec => {
                console.log(`  [${rec.priority}] ${rec.category}: ${rec.action}`);
            });
        }

        console.log('='.repeat(55));
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);

    if (args.length < 1) {
        console.log('Usage: node taiwan-localization-validator.js <design-path>');
        console.log('');
        console.log('Validates design documents for Taiwan localization compliance:');
        console.log('  - Traditional Chinese (zh-TW) language requirements');
        console.log('  - Taiwan emergency protocols (119, 110, 112, 113, 165)');
        console.log('  - Healthcare system integration (NHI, MOHW)');
        console.log('  - Service configuration for Taiwan region');
        console.log('  - Cultural sensitivity and local practices');
        process.exit(1);
    }

    const validator = new TaiwanLocalizationValidator();
    validator.validateDocument(args[0])
        .then(report => {
            const success = report.overall.includes('EXCELLENT') || report.overall.includes('GOOD');
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('❌ Taiwan localization validation failed:', error);
            process.exit(1);
        });
}

module.exports = TaiwanLocalizationValidator;