#!/usr/bin/env node

/**
 * Task-to-Specification Traceability System
 * Maps tasks to requirements, design elements, and implementation artifacts
 */

const fs = require('fs');
const path = require('path');

class TraceabilitySystem {
  constructor() {
    this.traceabilityMap = new Map();
    this.requirements = new Map();
    this.designElements = new Map();
    this.tasks = new Map();
    this.artifacts = new Map();
  }

  /**
   * Initialize traceability system by scanning spec directory
   */
  async initialize(specDirectory) {
    console.log(`🔍 Initializing traceability system for: ${specDirectory}`);

    // Load requirements
    await this.loadRequirements(specDirectory);

    // Load design elements
    await this.loadDesignElements(specDirectory);

    // Load tasks
    await this.loadTasks(specDirectory);

    // Build traceability matrix
    await this.buildTraceabilityMatrix();

    console.log('✅ Traceability system initialized');
    return this.generateTraceabilityReport();
  }

  /**
   * Load requirements from requirements.md
   */
  async loadRequirements(specDir) {
    const reqPath = path.join(specDir, 'requirements.md');

    if (!fs.existsSync(reqPath)) {
      console.warn(`⚠️ Requirements file not found: ${reqPath}`);
      return;
    }

    const content = fs.readFileSync(reqPath, 'utf-8');
    const reqPattern = /(?:^|\n)(?:##\s*)?(?:REQ-(\d+)[:.]?\s*(.+?)(?:\n|$))/gm;

    let match;
    while ((match = reqPattern.exec(content)) !== null) {
      const reqId = `REQ-${match[1]}`;
      const description = match[2].trim();

      this.requirements.set(reqId, {
        id: reqId,
        description,
        priority: this.extractPriority(description),
        category: this.categorizeRequirement(description),
        source: 'requirements.md',
        coveredBy: []
      });
    }

    console.log(`📋 Loaded ${this.requirements.size} requirements`);
  }

  /**
   * Load design elements from design.md
   */
  async loadDesignElements(specDir) {
    const designPath = path.join(specDir, 'design.md');

    if (!fs.existsSync(designPath)) {
      console.warn(`⚠️ Design file not found: ${designPath}`);
      return;
    }

    const content = fs.readFileSync(designPath, 'utf-8');

    // Extract components, APIs, data models
    this.extractComponents(content);
    this.extractAPIs(content);
    this.extractDataModels(content);

    console.log(`🏗️ Loaded ${this.designElements.size} design elements`);
  }

  /**
   * Extract component designs
   */
  extractComponents(content) {
    const componentPattern = /(?:^|\n)(?:##\s*)?(?:Component|Module|Service):\s*(.+?)(?:\n|$)/gmi;
    let match;

    while ((match = componentPattern.exec(content)) !== null) {
      const componentName = match[1].trim();
      const elementId = `COMP-${componentName.replace(/\s+/g, '-').toLowerCase()}`;

      this.designElements.set(elementId, {
        id: elementId,
        type: 'component',
        name: componentName,
        description: this.extractDescription(content, match.index),
        implementedBy: []
      });
    }
  }

  /**
   * Extract API designs
   */
  extractAPIs(content) {
    const apiPattern = /(?:^|\n)(?:##\s*)?(?:API|Endpoint):\s*(.+?)(?:\n|$)/gmi;
    let match;

    while ((match = apiPattern.exec(content)) !== null) {
      const apiName = match[1].trim();
      const elementId = `API-${apiName.replace(/\s+/g, '-').toLowerCase()}`;

      this.designElements.set(elementId, {
        id: elementId,
        type: 'api',
        name: apiName,
        description: this.extractDescription(content, match.index),
        implementedBy: []
      });
    }
  }

  /**
   * Extract data model designs
   */
  extractDataModels(content) {
    const modelPattern = /(?:^|\n)(?:##\s*)?(?:Model|Schema|Data):\s*(.+?)(?:\n|$)/gmi;
    let match;

    while ((match = modelPattern.exec(content)) !== null) {
      const modelName = match[1].trim();
      const elementId = `MODEL-${modelName.replace(/\s+/g, '-').toLowerCase()}`;

      this.designElements.set(elementId, {
        id: elementId,
        type: 'model',
        name: modelName,
        description: this.extractDescription(content, match.index),
        implementedBy: []
      });
    }
  }

  /**
   * Load tasks from task documents
   */
  async loadTasks(specDir) {
    const taskFiles = this.findTaskFiles(specDir);

    for (const taskFile of taskFiles) {
      await this.loadTasksFromFile(taskFile);
    }

    console.log(`📝 Loaded ${this.tasks.size} tasks`);
  }

  /**
   * Find all task files in spec directory
   */
  findTaskFiles(specDir) {
    const taskFiles = [];

    const searchDir = (dir) => {
      const items = fs.readdirSync(dir);

      for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);

        if (stat.isDirectory()) {
          searchDir(fullPath);
        } else if (item === 'tasks.md' || item.includes('task')) {
          taskFiles.push(fullPath);
        }
      }
    };

    searchDir(specDir);
    return taskFiles;
  }

  /**
   * Load tasks from a specific task file
   */
  async loadTasksFromFile(taskFile) {
    const content = fs.readFileSync(taskFile, 'utf-8');
    const taskPattern = /^-\s*\[\s*\]\s*(\d+)\.\s+(.+?)$/gm;

    let match;
    while ((match = taskPattern.exec(content)) !== null) {
      const taskId = `TASK-${path.basename(path.dirname(taskFile))}-${match[1]}`;
      const description = match[2].trim();

      const task = {
        id: taskId,
        number: parseInt(match[1]),
        description,
        file: taskFile,
        requirements: this.extractRequirementReferences(description),
        implements: this.extractImplementationReferences(description),
        files: this.extractFileReferences(description),
        medicalSafety: this.hasMedicalSafety(description)
      };

      this.tasks.set(taskId, task);
    }
  }

  /**
   * Extract requirement references from task description
   */
  extractRequirementReferences(description) {
    const reqPattern = /REQ-\d+/g;
    return description.match(reqPattern) || [];
  }

  /**
   * Extract implementation references
   */
  extractImplementationReferences(description) {
    const implementations = [];

    // Look for component/service references
    if (description.includes('component') || description.includes('service')) {
      implementations.push('component');
    }

    // Look for API references
    if (description.includes('api') || description.includes('endpoint')) {
      implementations.push('api');
    }

    // Look for model references
    if (description.includes('model') || description.includes('schema')) {
      implementations.push('model');
    }

    return implementations;
  }

  /**
   * Extract file references from task description
   */
  extractFileReferences(description) {
    const filePattern = /\b[\w\-\/]+\.\w+\b/g;
    return description.match(filePattern) || [];
  }

  /**
   * Check if task has medical safety considerations
   */
  hasMedicalSafety(description) {
    const medicalKeywords = ['symptom', 'diagnosis', 'medical', 'health', 'emergency', 'hospital'];
    return medicalKeywords.some(keyword =>
      description.toLowerCase().includes(keyword)
    );
  }

  /**
   * Build traceability matrix
   */
  async buildTraceabilityMatrix() {
    // Map requirements to tasks
    for (const [taskId, task] of this.tasks) {
      for (const reqId of task.requirements) {
        if (this.requirements.has(reqId)) {
          this.requirements.get(reqId).coveredBy.push(taskId);
        }
      }
    }

    // Map design elements to tasks
    for (const [taskId, task] of this.tasks) {
      for (const impl of task.implements) {
        for (const [elementId, element] of this.designElements) {
          if (element.type === impl) {
            element.implementedBy.push(taskId);
          }
        }
      }
    }

    console.log('🔗 Traceability matrix built');
  }

  /**
   * Validate traceability coverage
   */
  validateTraceability() {
    const results = {
      requirementsCoverage: 0,
      uncoveredRequirements: [],
      designCoverage: 0,
      unimplementedElements: [],
      orphanedTasks: [],
      medicalSafetyTasks: 0,
      overall: 'PASS'
    };

    // Check requirements coverage
    const uncoveredReqs = Array.from(this.requirements.values())
      .filter(req => req.coveredBy.length === 0);

    results.uncoveredRequirements = uncoveredReqs.map(req => req.id);
    results.requirementsCoverage =
      ((this.requirements.size - uncoveredReqs.length) / this.requirements.size) * 100;

    // Check design implementation coverage
    const unimplementedElements = Array.from(this.designElements.values())
      .filter(element => element.implementedBy.length === 0);

    results.unimplementedElements = unimplementedElements.map(element => element.id);
    results.designCoverage =
      ((this.designElements.size - unimplementedElements.length) / this.designElements.size) * 100;

    // Check for orphaned tasks (no requirement references)
    const orphanedTasks = Array.from(this.tasks.values())
      .filter(task => task.requirements.length === 0);

    results.orphanedTasks = orphanedTasks.map(task => task.id);

    // Count medical safety tasks
    results.medicalSafetyTasks = Array.from(this.tasks.values())
      .filter(task => task.medicalSafety).length;

    // Determine overall status
    if (results.requirementsCoverage < 80 || results.designCoverage < 70) {
      results.overall = 'MAJOR_ISSUES';
    } else if (results.requirementsCoverage < 95 || results.designCoverage < 90) {
      results.overall = 'NEEDS_IMPROVEMENT';
    }

    return results;
  }

  /**
   * Generate traceability report
   */
  generateTraceabilityReport() {
    const validation = this.validateTraceability();

    let report = '\n';
    report += '='.repeat(60) + '\n';
    report += '🔗 TRACEABILITY ANALYSIS REPORT\n';
    report += '='.repeat(60) + '\n';
    report += `Overall Status: ${validation.overall}\n`;
    report += `Requirements Coverage: ${validation.requirementsCoverage.toFixed(1)}%\n`;
    report += `Design Implementation: ${validation.designCoverage.toFixed(1)}%\n`;
    report += `Medical Safety Tasks: ${validation.medicalSafetyTasks}\n\n`;

    // Requirements analysis
    report += '📋 REQUIREMENTS ANALYSIS\n';
    report += '-'.repeat(30) + '\n';
    report += `Total Requirements: ${this.requirements.size}\n`;
    report += `Covered: ${this.requirements.size - validation.uncoveredRequirements.length}\n`;
    report += `Uncovered: ${validation.uncoveredRequirements.length}\n`;

    if (validation.uncoveredRequirements.length > 0) {
      report += '\nUncovered Requirements:\n';
      validation.uncoveredRequirements.forEach(reqId => {
        const req = this.requirements.get(reqId);
        report += `  • ${reqId}: ${req?.description || 'Unknown'}\n`;
      });
    }

    // Design analysis
    report += '\n🏗️ DESIGN IMPLEMENTATION ANALYSIS\n';
    report += '-'.repeat(30) + '\n';
    report += `Total Design Elements: ${this.designElements.size}\n`;
    report += `Implemented: ${this.designElements.size - validation.unimplementedElements.length}\n`;
    report += `Unimplemented: ${validation.unimplementedElements.length}\n`;

    if (validation.unimplementedElements.length > 0) {
      report += '\nUnimplemented Elements:\n';
      validation.unimplementedElements.forEach(elementId => {
        const element = this.designElements.get(elementId);
        report += `  • ${elementId}: ${element?.name || 'Unknown'}\n`;
      });
    }

    // Task analysis
    report += '\n📝 TASK ANALYSIS\n';
    report += '-'.repeat(30) + '\n';
    report += `Total Tasks: ${this.tasks.size}\n`;
    report += `Orphaned Tasks: ${validation.orphanedTasks.length}\n`;
    report += `Medical Safety Tasks: ${validation.medicalSafetyTasks}\n`;

    if (validation.orphanedTasks.length > 0) {
      report += '\nOrphaned Tasks (no requirement references):\n';
      validation.orphanedTasks.forEach(taskId => {
        const task = this.tasks.get(taskId);
        report += `  • ${taskId}: ${task?.description || 'Unknown'}\n`;
      });
    }

    // Medical safety analysis
    if (validation.medicalSafetyTasks > 0) {
      report += '\n🏥 MEDICAL SAFETY TASKS\n';
      report += '-'.repeat(30) + '\n';
      const medicalTasks = Array.from(this.tasks.values())
        .filter(task => task.medicalSafety);

      medicalTasks.forEach(task => {
        report += `  • ${task.id}: ${task.description}\n`;
      });
    }

    report += '\n' + '='.repeat(60) + '\n';

    return { validation, report };
  }

  /**
   * Generate requirements traceability matrix
   */
  generateTraceabilityMatrix() {
    const matrix = {
      requirements: {},
      design: {},
      tasks: {}
    };

    // Requirements to tasks mapping
    for (const [reqId, req] of this.requirements) {
      matrix.requirements[reqId] = {
        description: req.description,
        coveredBy: req.coveredBy,
        coverage: req.coveredBy.length > 0 ? 'COVERED' : 'UNCOVERED'
      };
    }

    // Design to tasks mapping
    for (const [elementId, element] of this.designElements) {
      matrix.design[elementId] = {
        type: element.type,
        name: element.name,
        implementedBy: element.implementedBy,
        status: element.implementedBy.length > 0 ? 'IMPLEMENTED' : 'PENDING'
      };
    }

    // Tasks mapping
    for (const [taskId, task] of this.tasks) {
      matrix.tasks[taskId] = {
        description: task.description,
        requirements: task.requirements,
        implements: task.implements,
        files: task.files,
        medicalSafety: task.medicalSafety
      };
    }

    return matrix;
  }

  /**
   * Export traceability data
   */
  exportTraceability(outputPath) {
    const data = {
      timestamp: new Date().toISOString(),
      summary: this.validateTraceability(),
      matrix: this.generateTraceabilityMatrix(),
      metadata: {
        requirementsCount: this.requirements.size,
        designElementsCount: this.designElements.size,
        tasksCount: this.tasks.size
      }
    };

    fs.writeFileSync(outputPath, JSON.stringify(data, null, 2));
    console.log(`📊 Traceability data exported to: ${outputPath}`);
  }

  /**
   * Helper methods
   */
  extractPriority(description) {
    if (description.toLowerCase().includes('critical') || description.toLowerCase().includes('high')) {
      return 'HIGH';
    } else if (description.toLowerCase().includes('low')) {
      return 'LOW';
    }
    return 'MEDIUM';
  }

  categorizeRequirement(description) {
    const desc = description.toLowerCase();
    if (desc.includes('medical') || desc.includes('health') || desc.includes('symptom')) {
      return 'medical';
    } else if (desc.includes('search') || desc.includes('location') || desc.includes('hospital')) {
      return 'location';
    } else if (desc.includes('ui') || desc.includes('interface') || desc.includes('user')) {
      return 'interface';
    } else if (desc.includes('security') || desc.includes('privacy') || desc.includes('auth')) {
      return 'security';
    }
    return 'functional';
  }

  extractDescription(content, startIndex) {
    const lines = content.substring(startIndex).split('\n');
    return lines.slice(0, 3).join(' ').trim().substring(0, 200) + '...';
  }
}

// CLI usage
if (require.main === module) {
  const command = process.argv[2];
  const specDir = process.argv[3] || 'spec';

  const traceability = new TraceabilitySystem();

  if (command === 'analyze') {
    traceability.initialize(specDir)
      .then(({ validation, report }) => {
        console.log(report);
        process.exit(validation.overall === 'PASS' ? 0 : 1);
      })
      .catch(error => {
        console.error('❌ Traceability analysis failed:', error.message);
        process.exit(1);
      });

  } else if (command === 'export') {
    const outputFile = process.argv[4] || 'traceability-report.json';

    traceability.initialize(specDir)
      .then(() => {
        traceability.exportTraceability(outputFile);
        console.log('✅ Traceability data exported');
      })
      .catch(error => {
        console.error('❌ Export failed:', error.message);
        process.exit(1);
      });

  } else {
    console.log('Task-to-Specification Traceability System');
    console.log('Usage:');
    console.log('  node traceability-system.js analyze [spec-dir]');
    console.log('  node traceability-system.js export [spec-dir] [output-file]');
    console.log('');
    console.log('Examples:');
    console.log('  node traceability-system.js analyze spec/');
    console.log('  node traceability-system.js export spec/ traceability.json');
  }
}

module.exports = TraceabilitySystem;