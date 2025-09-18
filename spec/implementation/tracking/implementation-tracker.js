/**
 * Implementation Tracker
 * Track implementation progress and quality metrics for medical AI tasks
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class ImplementationTracker {
  constructor(config = {}) {
    this.config = {
      projectRoot: config.projectRoot || process.cwd(),
      trackingFile: config.trackingFile || 'implementation-tracking.json',
      metricsFile: config.metricsFile || 'implementation-metrics.json',
      enableRealtimeTracking: config.enableRealtimeTracking !== false,
      ...config
    };

    this.trackingData = this.loadTrackingData();
    this.metrics = this.loadMetrics();
    this.sessionId = `session-${Date.now()}`;
  }

  /**
   * Start tracking a new implementation task
   */
  async startTask(taskId, taskSpec) {
    console.log(`📊 Starting tracking for task: ${taskId}`);

    const task = {
      id: taskId,
      title: taskSpec.title,
      description: taskSpec.description,
      type: taskSpec.type,
      priority: taskSpec.priority || 'medium',
      status: 'started',
      startTime: new Date().toISOString(),
      phases: {},
      metrics: {
        testCoverage: 0,
        codeQuality: 0,
        medicalSafety: 0,
        taiwanCompliance: 0,
        linesOfCode: 0,
        testCount: 0,
        implementationTime: 0
      },
      dependencies: taskSpec.dependencies || [],
      tags: taskSpec.tags || []
    };

    // Add medical AI specific tracking
    if (this.isMedicalTask(taskSpec)) {
      task.medicalTracking = {
        emergencyHandlingImplemented: false,
        medicalDisclaimersAdded: false,
        privacyProtectionImplemented: false,
        emergencyKeywordsDetection: false
      };
    }

    // Add Taiwan compliance specific tracking
    if (this.requiresTaiwanCompliance(taskSpec)) {
      task.taiwanTracking = {
        languageSupport: false,
        emergencyNumbers: false,
        pdpaCompliance: false,
        localizationComplete: false,
        timeZoneHandling: false
      };
    }

    this.trackingData.tasks[taskId] = task;
    await this.saveTrackingData();

    // Initialize real-time tracking
    if (this.config.enableRealtimeTracking) {
      await this.initializeRealtimeTracking(taskId);
    }

    return task;
  }

  /**
   * Update task progress
   */
  async updateTaskProgress(taskId, phase, progressData) {
    const task = this.trackingData.tasks[taskId];
    if (!task) {
      throw new Error(`Task ${taskId} not found in tracking data`);
    }

    const phaseData = {
      status: progressData.status,
      startTime: progressData.startTime || new Date().toISOString(),
      endTime: progressData.endTime,
      duration: progressData.duration,
      results: progressData.results || {},
      metrics: progressData.metrics || {}
    };

    task.phases[phase] = phaseData;
    task.lastUpdated = new Date().toISOString();

    // Update overall metrics
    await this.updateTaskMetrics(taskId, phase, progressData);

    // Update medical tracking if applicable
    if (task.medicalTracking) {
      await this.updateMedicalTracking(taskId, phase, progressData);
    }

    // Update Taiwan compliance tracking if applicable
    if (task.taiwanTracking) {
      await this.updateTaiwanTracking(taskId, phase, progressData);
    }

    await this.saveTrackingData();

    // Send real-time update
    if (this.config.enableRealtimeTracking) {
      await this.sendRealtimeUpdate(taskId, phase, phaseData);
    }

    console.log(`📈 Updated progress for ${taskId}: ${phase} - ${progressData.status}`);
  }

  /**
   * Complete a task
   */
  async completeTask(taskId, completionData = {}) {
    const task = this.trackingData.tasks[taskId];
    if (!task) {
      throw new Error(`Task ${taskId} not found in tracking data`);
    }

    task.status = 'completed';
    task.endTime = new Date().toISOString();
    task.duration = Date.now() - new Date(task.startTime).getTime();
    task.completionData = completionData;

    // Final metrics calculation
    await this.calculateFinalMetrics(taskId);

    // Validate completion criteria
    const validationResults = await this.validateTaskCompletion(taskId);
    task.validationResults = validationResults;

    if (!validationResults.allCriteriaMet) {
      task.status = 'completed-with-warnings';
      console.warn(`⚠️ Task ${taskId} completed with warnings:`, validationResults.warnings);
    }

    await this.saveTrackingData();

    // Update global metrics
    await this.updateGlobalMetrics(task);

    console.log(`✅ Task ${taskId} completed: ${task.title}`);

    return task;
  }

  /**
   * Update task metrics based on phase data
   */
  async updateTaskMetrics(taskId, phase, progressData) {
    const task = this.trackingData.tasks[taskId];

    switch (phase) {
      case 'testing':
        if (progressData.metrics?.testCoverage) {
          task.metrics.testCoverage = progressData.metrics.testCoverage;
        }
        if (progressData.metrics?.testCount) {
          task.metrics.testCount = progressData.metrics.testCount;
        }
        break;

      case 'implementation':
        if (progressData.metrics?.linesOfCode) {
          task.metrics.linesOfCode = progressData.metrics.linesOfCode;
        }
        if (progressData.metrics?.codeQuality) {
          task.metrics.codeQuality = progressData.metrics.codeQuality;
        }
        break;

      case 'medical-safety':
        if (progressData.metrics?.safetyScore) {
          task.metrics.medicalSafety = progressData.metrics.safetyScore;
        }
        break;

      case 'taiwan-compliance':
        if (progressData.metrics?.complianceScore) {
          task.metrics.taiwanCompliance = progressData.metrics.complianceScore;
        }
        break;
    }

    // Update implementation time
    if (progressData.startTime && progressData.endTime) {
      const phaseTime = new Date(progressData.endTime) - new Date(progressData.startTime);
      task.metrics.implementationTime += phaseTime;
    }
  }

  /**
   * Update medical-specific tracking
   */
  async updateMedicalTracking(taskId, phase, progressData) {
    const task = this.trackingData.tasks[taskId];

    if (phase === 'medical-safety' || phase === 'implementation') {
      if (progressData.results?.emergencyHandling) {
        task.medicalTracking.emergencyHandlingImplemented = true;
      }

      if (progressData.results?.medicalDisclaimers) {
        task.medicalTracking.medicalDisclaimersAdded = true;
      }

      if (progressData.results?.privacyProtection) {
        task.medicalTracking.privacyProtectionImplemented = true;
      }

      if (progressData.results?.emergencyKeywords) {
        task.medicalTracking.emergencyKeywordsDetection = true;
      }
    }
  }

  /**
   * Update Taiwan compliance tracking
   */
  async updateTaiwanTracking(taskId, phase, progressData) {
    const task = this.trackingData.tasks[taskId];

    if (phase === 'taiwan-compliance' || phase === 'implementation') {
      if (progressData.results?.languageSupport) {
        task.taiwanTracking.languageSupport = true;
      }

      if (progressData.results?.emergencyNumbers) {
        task.taiwanTracking.emergencyNumbers = true;
      }

      if (progressData.results?.pdpaCompliance) {
        task.taiwanTracking.pdpaCompliance = true;
      }

      if (progressData.results?.localization) {
        task.taiwanTracking.localizationComplete = true;
      }

      if (progressData.results?.timeZone) {
        task.taiwanTracking.timeZoneHandling = true;
      }
    }
  }

  /**
   * Calculate final metrics for completed task
   */
  async calculateFinalMetrics(taskId) {
    const task = this.trackingData.tasks[taskId];

    // Calculate overall quality score
    const qualityMetrics = [
      task.metrics.testCoverage,
      task.metrics.codeQuality,
      task.metrics.medicalSafety,
      task.metrics.taiwanCompliance
    ].filter(metric => metric > 0);

    task.metrics.overallQuality = qualityMetrics.length > 0 ?
      qualityMetrics.reduce((sum, metric) => sum + metric, 0) / qualityMetrics.length : 0;

    // Calculate velocity (story points per hour)
    const storyPoints = this.estimateStoryPoints(task);
    const hoursSpent = task.metrics.implementationTime / (1000 * 60 * 60);
    task.metrics.velocity = hoursSpent > 0 ? storyPoints / hoursSpent : 0;

    // Calculate completion rate based on phases
    const totalPhases = Object.keys(task.phases).length;
    const completedPhases = Object.values(task.phases).filter(phase => phase.status === 'completed').length;
    task.metrics.completionRate = totalPhases > 0 ? (completedPhases / totalPhases) * 100 : 0;
  }

  /**
   * Validate task completion criteria
   */
  async validateTaskCompletion(taskId) {
    const task = this.trackingData.tasks[taskId];
    const warnings = [];
    const errors = [];

    // Check minimum test coverage
    if (task.metrics.testCoverage < 80) {
      warnings.push(`Test coverage ${task.metrics.testCoverage}% below recommended 80%`);
    }

    // Check medical safety for medical tasks
    if (task.medicalTracking) {
      if (!task.medicalTracking.emergencyHandlingImplemented) {
        errors.push('Emergency handling not implemented for medical task');
      }

      if (!task.medicalTracking.medicalDisclaimersAdded) {
        errors.push('Medical disclaimers not added for medical task');
      }

      if (task.metrics.medicalSafety < 90) {
        warnings.push(`Medical safety score ${task.metrics.medicalSafety}% below recommended 90%`);
      }
    }

    // Check Taiwan compliance
    if (task.taiwanTracking) {
      if (!task.taiwanTracking.languageSupport) {
        errors.push('Taiwan language support not implemented');
      }

      if (!task.taiwanTracking.emergencyNumbers) {
        warnings.push('Taiwan emergency numbers not configured');
      }

      if (task.metrics.taiwanCompliance < 90) {
        warnings.push(`Taiwan compliance score ${task.metrics.taiwanCompliance}% below recommended 90%`);
      }
    }

    // Check code quality
    if (task.metrics.codeQuality < 70) {
      warnings.push(`Code quality score ${task.metrics.codeQuality}% below recommended 70%`);
    }

    return {
      allCriteriaMet: errors.length === 0,
      hasWarnings: warnings.length > 0,
      errors,
      warnings,
      overallScore: task.metrics.overallQuality
    };
  }

  /**
   * Generate progress report
   */
  async generateProgressReport(taskId = null) {
    if (taskId) {
      return this.generateTaskReport(taskId);
    }

    // Generate overall project report
    const tasks = Object.values(this.trackingData.tasks);
    const completedTasks = tasks.filter(task => task.status === 'completed');
    const inProgressTasks = tasks.filter(task => task.status === 'in-progress');

    const report = {
      summary: {
        totalTasks: tasks.length,
        completedTasks: completedTasks.length,
        inProgressTasks: inProgressTasks.length,
        completionRate: tasks.length > 0 ? (completedTasks.length / tasks.length) * 100 : 0
      },
      metrics: {
        averageTestCoverage: this.calculateAverageMetric(tasks, 'testCoverage'),
        averageCodeQuality: this.calculateAverageMetric(tasks, 'codeQuality'),
        averageMedicalSafety: this.calculateAverageMetric(tasks, 'medicalSafety'),
        averageTaiwanCompliance: this.calculateAverageMetric(tasks, 'taiwanCompliance'),
        totalLinesOfCode: tasks.reduce((sum, task) => sum + task.metrics.linesOfCode, 0),
        totalTestCount: tasks.reduce((sum, task) => sum + task.metrics.testCount, 0)
      },
      medicalCompliance: this.calculateMedicalComplianceStats(tasks),
      taiwanCompliance: this.calculateTaiwanComplianceStats(tasks),
      trends: await this.calculateTrends(),
      recommendations: this.generateRecommendations(tasks)
    };

    return report;
  }

  /**
   * Generate task-specific report
   */
  generateTaskReport(taskId) {
    const task = this.trackingData.tasks[taskId];
    if (!task) {
      throw new Error(`Task ${taskId} not found`);
    }

    const report = {
      task: {
        id: task.id,
        title: task.title,
        status: task.status,
        duration: task.duration,
        phases: task.phases
      },
      metrics: task.metrics,
      medicalTracking: task.medicalTracking,
      taiwanTracking: task.taiwanTracking,
      validationResults: task.validationResults,
      timeline: this.generateTaskTimeline(task),
      achievements: this.identifyTaskAchievements(task),
      areasForImprovement: this.identifyImprovementAreas(task)
    };

    return report;
  }

  /**
   * Real-time tracking initialization
   */
  async initializeRealtimeTracking(taskId) {
    try {
      await this.execCommand(`npx claude-flow@alpha hooks notify --message "Started tracking task ${taskId}" --type "info"`);
    } catch (error) {
      console.warn('Could not initialize real-time tracking:', error.message);
    }
  }

  /**
   * Send real-time update
   */
  async sendRealtimeUpdate(taskId, phase, phaseData) {
    try {
      const message = `Task ${taskId}: ${phase} ${phaseData.status}`;
      await this.execCommand(`npx claude-flow@alpha hooks notify --message "${message}" --type "progress"`);
    } catch (error) {
      console.warn('Could not send real-time update:', error.message);
    }
  }

  /**
   * Update global project metrics
   */
  async updateGlobalMetrics(completedTask) {
    this.metrics.totalTasksCompleted++;
    this.metrics.totalImplementationTime += completedTask.metrics.implementationTime;
    this.metrics.totalLinesOfCode += completedTask.metrics.linesOfCode;
    this.metrics.totalTestCount += completedTask.metrics.testCount;

    // Update quality averages
    const completedTasks = Object.values(this.trackingData.tasks).filter(task => task.status === 'completed');
    this.metrics.averageTestCoverage = this.calculateAverageMetric(completedTasks, 'testCoverage');
    this.metrics.averageCodeQuality = this.calculateAverageMetric(completedTasks, 'codeQuality');
    this.metrics.averageMedicalSafety = this.calculateAverageMetric(completedTasks, 'medicalSafety');
    this.metrics.averageTaiwanCompliance = this.calculateAverageMetric(completedTasks, 'taiwanCompliance');

    // Update velocity
    const totalStoryPoints = completedTasks.reduce((sum, task) => sum + this.estimateStoryPoints(task), 0);
    const totalHours = this.metrics.totalImplementationTime / (1000 * 60 * 60);
    this.metrics.averageVelocity = totalHours > 0 ? totalStoryPoints / totalHours : 0;

    await this.saveMetrics();
  }

  // Utility methods

  loadTrackingData() {
    const trackingPath = path.join(this.config.projectRoot, this.config.trackingFile);
    if (fs.existsSync(trackingPath)) {
      return JSON.parse(fs.readFileSync(trackingPath, 'utf8'));
    }

    return {
      tasks: {},
      metadata: {
        created: new Date().toISOString(),
        version: '1.0.0'
      }
    };
  }

  loadMetrics() {
    const metricsPath = path.join(this.config.projectRoot, this.config.metricsFile);
    if (fs.existsSync(metricsPath)) {
      return JSON.parse(fs.readFileSync(metricsPath, 'utf8'));
    }

    return {
      totalTasksCompleted: 0,
      totalImplementationTime: 0,
      totalLinesOfCode: 0,
      totalTestCount: 0,
      averageTestCoverage: 0,
      averageCodeQuality: 0,
      averageMedicalSafety: 0,
      averageTaiwanCompliance: 0,
      averageVelocity: 0,
      lastUpdated: new Date().toISOString()
    };
  }

  async saveTrackingData() {
    const trackingPath = path.join(this.config.projectRoot, this.config.trackingFile);
    this.trackingData.metadata.lastUpdated = new Date().toISOString();
    fs.writeFileSync(trackingPath, JSON.stringify(this.trackingData, null, 2));
  }

  async saveMetrics() {
    const metricsPath = path.join(this.config.projectRoot, this.config.metricsFile);
    this.metrics.lastUpdated = new Date().toISOString();
    fs.writeFileSync(metricsPath, JSON.stringify(this.metrics, null, 2));
  }

  isMedicalTask(taskSpec) {
    const medicalKeywords = ['medical', 'health', 'symptom', 'triage', 'hospital', 'emergency'];
    const content = (taskSpec.title + ' ' + taskSpec.description).toLowerCase();
    return medicalKeywords.some(keyword => content.includes(keyword));
  }

  requiresTaiwanCompliance(taskSpec) {
    const taiwanKeywords = ['taiwan', 'zh-tw', 'localization', 'emergency numbers', 'pdpa'];
    const content = (taskSpec.title + ' ' + taskSpec.description).toLowerCase();
    return taiwanKeywords.some(keyword => content.includes(keyword)) || this.isMedicalTask(taskSpec);
  }

  calculateAverageMetric(tasks, metricName) {
    const validTasks = tasks.filter(task => task.metrics[metricName] > 0);
    if (validTasks.length === 0) return 0;

    return validTasks.reduce((sum, task) => sum + task.metrics[metricName], 0) / validTasks.length;
  }

  estimateStoryPoints(task) {
    // Simple story point estimation based on task complexity
    let points = 1; // Base point

    if (task.type === 'api_endpoint') points += 2;
    if (task.type === 'service') points += 3;
    if (task.medicalTracking) points += 2; // Medical tasks are more complex
    if (task.taiwanTracking) points += 1; // Localization adds complexity

    return points;
  }

  calculateMedicalComplianceStats(tasks) {
    const medicalTasks = tasks.filter(task => task.medicalTracking);
    if (medicalTasks.length === 0) return null;

    return {
      totalMedicalTasks: medicalTasks.length,
      emergencyHandlingCompliance: medicalTasks.filter(task => task.medicalTracking.emergencyHandlingImplemented).length,
      disclaimerCompliance: medicalTasks.filter(task => task.medicalTracking.medicalDisclaimersAdded).length,
      privacyCompliance: medicalTasks.filter(task => task.medicalTracking.privacyProtectionImplemented).length,
      overallComplianceRate: this.calculateAverageMetric(medicalTasks, 'medicalSafety')
    };
  }

  calculateTaiwanComplianceStats(tasks) {
    const taiwanTasks = tasks.filter(task => task.taiwanTracking);
    if (taiwanTasks.length === 0) return null;

    return {
      totalTaiwanTasks: taiwanTasks.length,
      languageCompliance: taiwanTasks.filter(task => task.taiwanTracking.languageSupport).length,
      emergencyNumbersCompliance: taiwanTasks.filter(task => task.taiwanTracking.emergencyNumbers).length,
      pdpaCompliance: taiwanTasks.filter(task => task.taiwanTracking.pdpaCompliance).length,
      overallComplianceRate: this.calculateAverageMetric(taiwanTasks, 'taiwanCompliance')
    };
  }

  async calculateTrends() {
    // Simple trend calculation - could be enhanced with time-series analysis
    return {
      codeQualityTrend: 'improving',
      testCoverageTrend: 'stable',
      velocityTrend: 'improving',
      medicalSafetyTrend: 'stable'
    };
  }

  generateRecommendations(tasks) {
    const recommendations = [];

    const avgTestCoverage = this.calculateAverageMetric(tasks, 'testCoverage');
    if (avgTestCoverage < 80) {
      recommendations.push({
        type: 'test_coverage',
        priority: 'high',
        message: 'Increase test coverage to meet 80% threshold'
      });
    }

    const medicalTasks = tasks.filter(task => task.medicalTracking);
    const medicalComplianceRate = medicalTasks.length > 0 ?
      medicalTasks.filter(task => task.medicalTracking.emergencyHandlingImplemented).length / medicalTasks.length * 100 : 100;

    if (medicalComplianceRate < 100) {
      recommendations.push({
        type: 'medical_safety',
        priority: 'critical',
        message: 'Ensure all medical tasks implement emergency handling'
      });
    }

    return recommendations;
  }

  generateTaskTimeline(task) {
    return Object.entries(task.phases).map(([phase, data]) => ({
      phase,
      startTime: data.startTime,
      endTime: data.endTime,
      duration: data.duration,
      status: data.status
    }));
  }

  identifyTaskAchievements(task) {
    const achievements = [];

    if (task.metrics.testCoverage >= 90) {
      achievements.push('High Test Coverage');
    }

    if (task.metrics.codeQuality >= 90) {
      achievements.push('Excellent Code Quality');
    }

    if (task.medicalTracking && task.metrics.medicalSafety >= 95) {
      achievements.push('Outstanding Medical Safety');
    }

    if (task.taiwanTracking && task.metrics.taiwanCompliance >= 95) {
      achievements.push('Perfect Taiwan Compliance');
    }

    return achievements;
  }

  identifyImprovementAreas(task) {
    const areas = [];

    if (task.metrics.testCoverage < 80) {
      areas.push('Test Coverage');
    }

    if (task.metrics.codeQuality < 70) {
      areas.push('Code Quality');
    }

    if (task.medicalTracking && !task.medicalTracking.emergencyHandlingImplemented) {
      areas.push('Emergency Handling');
    }

    if (task.taiwanTracking && !task.taiwanTracking.languageSupport) {
      areas.push('Language Support');
    }

    return areas;
  }

  async execCommand(command) {
    return new Promise((resolve, reject) => {
      const child = spawn('cmd', ['/c', command], {
        cwd: this.config.projectRoot,
        stdio: 'pipe'
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
          resolve(stdout);
        } else {
          reject(new Error(stderr || `Command failed with code ${code}`));
        }
      });
    });
  }
}

module.exports = ImplementationTracker;