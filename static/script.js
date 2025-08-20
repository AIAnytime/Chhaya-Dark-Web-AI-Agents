class ChhayaOSInterface {
    constructor() {
        this.apiBase = 'http://localhost:8000/api/v1';
        this.currentJobId = null;
        this.updateInterval = null;
        this.init();
    }

    init() {
        this.updateTime();
        this.setupEventListeners();
        this.checkSystemStatus();
        
        // Update time every second
        setInterval(() => this.updateTime(), 1000);
        
        // Check system status every 5 seconds
        setInterval(() => this.checkSystemStatus(), 5000);
    }

    updateTime() {
        const now = new Date();
        const timeString = now.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        document.getElementById('current-time').textContent = timeString;
    }

    setupEventListeners() {
        const startButton = document.getElementById('start-scan');
        const searchInput = document.getElementById('search-query');
        const presetTags = document.querySelectorAll('.preset-tag');
        
        startButton.addEventListener('click', () => this.startScan());
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.startScan();
            }
        });

        // Add click handlers for preset tags
        presetTags.forEach(tag => {
            tag.addEventListener('click', () => {
                const keyword = tag.getAttribute('data-keyword');
                searchInput.value = keyword;
                searchInput.focus();
            });
        });
    }

    async checkSystemStatus() {
        try {
            // Check Tor status
            const torResponse = await fetch(`${this.apiBase}/crawler/tor/status`);
            const torData = await torResponse.json();
            this.updateTorStatus(torData);

            // Check system health
            const healthResponse = await fetch(`${this.apiBase}/monitoring/health`);
            const healthData = await healthResponse.json();
            this.updateSystemHealth(healthData);

            // Get monitoring stats
            const statsResponse = await fetch(`${this.apiBase}/monitoring/stats`);
            const statsData = await statsResponse.json();
            this.updateStats(statsData);

        } catch (error) {
            this.logMessage('System status check failed', 'error');
            console.error('Status check error:', error);
        }
    }

    updateTorStatus(data) {
        const indicator = document.getElementById('tor-indicator');
        const status = document.getElementById('tor-status');
        const ip = document.getElementById('tor-ip');
        const dot = indicator.querySelector('.pulse-dot');

        if (data.status === 'connected') {
            status.textContent = 'OPERATIONAL';
            ip.textContent = data.ip || 'MASKED';
            dot.className = 'pulse-dot';
            dot.style.background = '#00ff41';
            dot.style.boxShadow = '0 0 10px #00ff41';
        } else {
            status.textContent = 'DISCONNECTED';
            ip.textContent = 'UNAVAILABLE';
            dot.className = 'pulse-dot danger';
            dot.style.background = '#dc143c';
            dot.style.boxShadow = '0 0 10px #dc143c';
        }
    }

    updateSystemHealth(data) {
        const aiStatus = document.getElementById('ai-status');
        const aiIndicator = document.getElementById('ai-indicator').querySelector('.pulse-dot');

        if (data.status === 'healthy') {
            aiStatus.textContent = 'ON DUTY';
            aiIndicator.style.background = '#00ff41';
            aiIndicator.style.boxShadow = '0 0 10px #00ff41';
        } else {
            aiStatus.textContent = 'DEGRADED';
            aiIndicator.style.background = '#ff8c00';
            aiIndicator.style.boxShadow = '0 0 10px #ff8c00';
        }
    }

    updateStats(data) {
        document.getElementById('active-jobs').textContent = data.active_crawls || 0;
        document.getElementById('pages-crawled').textContent = data.total_pages_crawled || 0;
        document.getElementById('ai-analyses').textContent = data.total_analyses || 0;

        // Update crawler status
        const crawlerStatus = document.getElementById('crawler-status');
        const crawlerDot = document.getElementById('crawler-indicator').querySelector('.pulse-dot');
        
        if (data.active_crawls > 0) {
            crawlerStatus.textContent = 'ACTIVE SCAN';
            crawlerDot.style.background = '#ff4500';
            crawlerDot.style.boxShadow = '0 0 10px #ff4500';
        } else {
            crawlerStatus.textContent = 'STANDBY';
            crawlerDot.style.background = '#00ff41';
            crawlerDot.style.boxShadow = '0 0 10px #00ff41';
        }

        // Update threat level (placeholder logic)
        this.updateThreatLevel(data);
    }

    updateThreatLevel(data) {
        const riskScore = Math.min(100, (data.total_pages_crawled || 0) * 2);
        const threatBar = document.getElementById('threat-bar');
        const riskScoreElement = document.getElementById('risk-score');
        const threatClass = document.getElementById('threat-class');

        threatBar.style.width = `${riskScore}%`;
        riskScoreElement.textContent = `${riskScore}/100`;

        if (riskScore < 25) {
            threatClass.textContent = 'MINIMAL';
            threatClass.style.color = '#00ff41';
        } else if (riskScore < 50) {
            threatClass.textContent = 'MODERATE';
            threatClass.style.color = '#ff8c00';
        } else if (riskScore < 75) {
            threatClass.textContent = 'ELEVATED';
            threatClass.style.color = '#ff4500';
        } else {
            threatClass.textContent = 'CRITICAL';
            threatClass.style.color = '#dc143c';
        }
    }

    async startScan() {
        const query = document.getElementById('search-query').value.trim();
        const limit = parseInt(document.getElementById('crawl-limit').value) || 10;
        const button = document.getElementById('start-scan');

        if (!query) {
            this.logMessage('Search query required', 'error');
            return;
        }

        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> DEPLOYING...';

        try {
            this.logMessage(`Initiating dark web scan for: "${query}"`);
            
            const response = await fetch(`${this.apiBase}/crawler/crawl`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    limit: limit
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.currentJobId = data.job_id;
                this.logMessage(`Crawl job initiated: ${data.job_id}`);
                this.logMessage('Deploying spider agents to dark web...');
                
                // Start monitoring the job
                this.startJobMonitoring();
                
            } else {
                throw new Error(data.detail || 'Scan initiation failed');
            }

        } catch (error) {
            this.logMessage(`Scan failed: ${error.message}`, 'error');
            console.error('Scan error:', error);
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-rocket"></i> DEPLOY CRAWLERS';
        }
    }

    startJobMonitoring() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(async () => {
            if (this.currentJobId) {
                await this.updateJobStatus();
            }
        }, 3000);
    }

    async updateJobStatus() {
        try {
            const response = await fetch(`${this.apiBase}/crawler/crawl/${this.currentJobId}`);
            const jobData = await response.json();

            if (response.ok) {
                this.updateJobDisplay(jobData);
                
                if (jobData.status === 'completed' || jobData.status === 'failed') {
                    clearInterval(this.updateInterval);
                    this.updateInterval = null;
                    
                    // Re-enable the deploy button
                    const button = document.getElementById('deployBtn');
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-rocket"></i> DEPLOY CRAWLERS';
                    
                    if (jobData.status === 'completed') {
                        this.logMessage('Scan completed successfully');
                        this.startAnalysis();
                    } else {
                        this.logMessage('Scan failed', 'error');
                    }
                }
            }
        } catch (error) {
            console.error('Job status update error:', error);
        }
    }

    updateJobDisplay(jobData) {
        document.getElementById('links-found').textContent = jobData.total_links || 0;
        
        // Calculate success rate based on crawled vs attempted (not total found)
        const crawlLimit = parseInt(document.getElementById('crawl-limit').value) || 10;
        const attemptedCrawls = Math.min(jobData.total_links || 0, crawlLimit);
        const successRate = attemptedCrawls > 0 
            ? Math.round((jobData.crawled_links / attemptedCrawls) * 100)
            : 0;
        document.getElementById('success-rate').textContent = `${successRate}%`;

        // Debug logging
        console.log('DEBUG: Job data received:', jobData);
        console.log('DEBUG: Analysis results:', jobData.analysis_results);

        // Update AI agents card with analysis count
        if (jobData.analysis_results && jobData.analysis_results.length > 0) {
            const analysesElement = document.getElementById('ai-analyses');
            if (analysesElement) {
                analysesElement.textContent = jobData.analysis_results.length;
            }
        }

        // Check if AI analysis results are available
        if (jobData.analysis_results && jobData.analysis_results.length > 0) {
            console.log('DEBUG: Displaying analysis results');
            this.displayAnalysisResults(jobData.analysis_results);
        } else {
            console.log('DEBUG: No analysis results, displaying crawled data');
            // Update results display with crawled data
            this.displayResults(jobData);
        }
    }

    displayResults(jobData) {
        const container = document.getElementById('results-container');
        const crawlLimit = parseInt(document.getElementById('crawl-limit').value) || 10;
        const targetCrawls = Math.min(jobData.total_links || 0, crawlLimit);
        
        if (!jobData.pages || jobData.pages.length === 0) {
            container.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-search"></i>
                    <p>Scanning in progress... ${jobData.crawled_links || 0}/${targetCrawls} sites crawled</p>
                    <p style="font-size: 0.8rem; color: #666; margin-top: 10px;">
                        Found ${jobData.total_links || 0} total links, crawling ${targetCrawls}
                    </p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        
        jobData.pages.forEach((page, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            
            const preview = page.text_content.substring(0, 200) + '...';
            
            resultItem.innerHTML = `
                <div class="result-header">
                    <div class="result-url">${page.url}</div>
                    <div class="result-status status-success">CRAWLED</div>
                </div>
                <div class="result-details">
                    <strong>Title:</strong> ${page.title || 'No title'}<br>
                    <strong>Content Preview:</strong> ${preview}<br>
                    <strong>Images Found:</strong> ${page.images.length}<br>
                    <strong>Timestamp:</strong> ${new Date(page.crawl_timestamp).toLocaleString()}
                </div>
            `;
            
            container.appendChild(resultItem);
        });
    }

    async startAnalysis() {
        if (!this.currentJobId) return;

        try {
            this.logMessage('Initiating AI analysis of crawled data...');
            
            const response = await fetch(`${this.apiBase}/analysis/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    crawl_id: this.currentJobId,
                    analysis_type: 'full'
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.logMessage('AI analysis completed');
                this.displayAnalysisResults(data);
            } else {
                throw new Error(data.detail || 'Analysis failed');
            }

        } catch (error) {
            this.logMessage(`Analysis failed: ${error.message}`, 'error');
            console.error('Analysis error:', error);
        }
    }

    displayAnalysisResults(analysisData) {
        if (!analysisData || analysisData.length === 0) {
            return;
        }

        const container = document.getElementById('results-container');
        
        // Clear container and rebuild with analysis results
        container.innerHTML = '';
        
        analysisData.forEach((analysis, index) => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            
            const preview = analysis.summary || 'No summary available';
            const keywords = analysis.keywords && Array.isArray(analysis.keywords) 
                ? analysis.keywords.join(', ') 
                : 'No keywords';
            
            resultItem.innerHTML = `
                <div class="result-header">
                    <div class="result-url">${analysis.url || 'Unknown URL'}</div>
                    <div class="result-status status-analyzing">ANALYZED</div>
                </div>
                <div class="result-details">
                    <strong>Title:</strong> ${analysis.title || 'No title'}<br>
                    <strong>Content Preview:</strong> ${preview}<br>
                    <strong>Images Found:</strong> 0<br>
                    <strong>Timestamp:</strong> ${analysis.analysis_timestamp ? new Date(analysis.analysis_timestamp).toLocaleString() : 'Unknown'}<br>
                    <strong>Risk Level:</strong> ${analysis.risk_assessment?.level?.toUpperCase() || 'UNKNOWN'}<br>
                    <strong>Risk Score:</strong> ${analysis.risk_assessment?.score || 0}/100<br>
                    <strong>Category:</strong> ${analysis.risk_assessment?.category || 'Unspecified'}<br>
                    <strong>Keywords:</strong> ${keywords}<br>
                    <strong>Summary:</strong> ${analysis.summary || 'No summary available'}
                </div>
            `;
            
            container.appendChild(resultItem);
        });

        // Update threat level based on analysis
        this.updateThreatLevelFromAnalysisResults(analysisData);
    }

    updateThreatLevelFromAnalysisResults(analysisData) {
        if (!analysisData || analysisData.length === 0) return;

        // Calculate threat level from analysis results
        let totalScore = 0;
        let highRiskCount = 0;
        let criticalRiskCount = 0;

        analysisData.forEach(analysis => {
            totalScore += analysis.risk_assessment.score;
            if (analysis.risk_assessment.level === 'high') highRiskCount++;
            if (analysis.risk_assessment.level === 'critical') criticalRiskCount++;
        });

        const avgScore = totalScore / analysisData.length;
        
        const threatBar = document.getElementById('threat-bar');
        const riskScoreElement = document.getElementById('risk-score');
        const threatClass = document.getElementById('threat-class');

        if (threatBar && riskScoreElement && threatClass) {
            threatBar.style.width = `${avgScore}%`;
            riskScoreElement.textContent = Math.round(avgScore);

            if (criticalRiskCount > 0) {
                threatBar.className = 'threat-bar critical';
                threatClass.textContent = 'CRITICAL';
            } else if (highRiskCount > 0 || avgScore >= 60) {
                threatBar.className = 'threat-bar high';
                threatClass.textContent = 'HIGH';
            } else if (avgScore >= 30) {
                threatBar.className = 'threat-bar medium';
                threatClass.textContent = 'MEDIUM';
            } else {
                threatBar.className = 'threat-bar low';
                threatClass.textContent = 'LOW';
            }
        }
    }

    updateThreatLevelFromAnalysis(stats) {
        const riskDistribution = stats.risk_distribution;
        const totalPages = stats.total_pages_analyzed;
        
        if (totalPages === 0) return;

        const weightedScore = (
            (riskDistribution.low * 10) +
            (riskDistribution.medium * 30) +
            (riskDistribution.high * 60) +
            (riskDistribution.critical * 100)
        ) / totalPages;

        const threatBar = document.getElementById('threat-bar');
        const riskScoreElement = document.getElementById('risk-score');
        const threatClass = document.getElementById('threat-class');

        threatBar.style.width = `${weightedScore}%`;
        riskScoreElement.textContent = `${Math.round(weightedScore)}/100`;

        if (weightedScore < 25) {
            threatClass.textContent = 'MINIMAL';
            threatClass.style.color = '#00ff41';
        } else if (weightedScore < 50) {
            threatClass.textContent = 'MODERATE';
            threatClass.style.color = '#ff8c00';
        } else if (weightedScore < 75) {
            threatClass.textContent = 'ELEVATED';
            threatClass.style.color = '#ff4500';
        } else {
            threatClass.textContent = 'CRITICAL';
            threatClass.style.color = '#dc143c';
        }
    }

    logMessage(message, type = 'info') {
        const logContainer = document.getElementById('log-container');
        const timestamp = new Date().toLocaleTimeString();
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.innerHTML = `
            <span class="timestamp">[${timestamp}]</span>
            <span class="message">${message}</span>
        `;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;

        // Keep only last 50 log entries
        const entries = logContainer.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[0].remove();
        }
    }
}

// Initialize the interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChhayaOSInterface();
});
