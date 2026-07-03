const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const os = require('os');

const BASE_URL = process.env.TEST_URL || 'http://localhost:8000';
const OUTPUT_DIR = path.join(__dirname, '../test-results');
const TEST_DURATION = parseInt(process.env.TEST_DURATION || '300');
const CONCURRENT_USERS = parseInt(process.env.CONCURRENT_USERS || '50');

fs.mkdirSync(OUTPUT_DIR, { recursive: true });

function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getRandomElement(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

const userScenarios = [
    {
        name: 'caselaw_search',
        weight: 30,
        actions: [
            { method: 'GET', path: '/api/cases?page=1&limit=20', delay: 1000 },
            { method: 'GET', path: '/api/cases/search?q=contract', delay: 2000 },
            { method: 'GET', path: '/api/cases/1', delay: 1500 }
        ]
    },
    {
        name: 'lawyer_search',
        weight: 25,
        actions: [
            { method: 'GET', path: '/api/laws/search?q=知识产权', delay: 1500 },
            { method: 'GET', path: '/api/companies/search?q=科技', delay: 1000 },
            { method: 'GET', path: '/api/marketplace/lawyers', delay: 2000 }
        ]
    },
    {
        name: 'contract_review',
        weight: 20,
        actions: [
            { method: 'GET', path: '/api/contract/templates', delay: 1000 },
            { method: 'GET', path: '/api/contract/review/1', delay: 3000 },
            { method: 'GET', path: '/api/doc-gen/templates', delay: 1500 }
        ]
    },
    {
        name: 'backlog_management',
        weight: 15,
        actions: [
            { method: 'GET', path: '/api/backlog', delay: 1000 },
            { method: 'GET', path: '/api/schedule', delay: 1500 },
            { method: 'GET', path: '/api/clients', delay: 1000 }
        ]
    },
    {
        name: 'dashboard',
        weight: 10,
        actions: [
            { method: 'GET', path: '/api/health', delay: 500 },
            { method: 'GET', path: '/api/stats', delay: 2000 },
            { method: 'GET', path: '/api/backlog', delay: 1000 }
        ]
    }
];

const allActions = [];
userScenarios.forEach(scenario => {
    for (let i = 0; i < scenario.weight; i++) {
        allActions.push(...scenario.actions);
    }
});

async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function makeRequest(url, method = 'GET') {
    return new Promise((resolve) => {
        const start = Date.now();
        const parsedUrl = new URL(url);
        const options = {
            hostname: parsedUrl.hostname,
            port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
            path: parsedUrl.pathname + parsedUrl.search,
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'LexPrime Load Test Client'
            }
        };

        const protocol = parsedUrl.protocol === 'https:' ? https : http;
        const req = protocol.request(options, (res) => {
            let data = '';
            res.on('data', (chunk) => { data += chunk; });
            res.on('end', () => {
                const duration = Date.now() - start;
                resolve({
                    status: res.statusCode,
                    duration,
                    url,
                    method,
                    size: data.length
                });
            });
        });

        req.on('error', (e) => {
            const duration = Date.now() - start;
            resolve({
                status: 0,
                duration,
                url,
                method,
                error: e.message
            });
        });

        req.end();
    });
}

async function simulateUser(userId) {
    const results = [];
    const startTime = Date.now();

    while (Date.now() - startTime < TEST_DURATION * 1000) {
        const action = getRandomElement(allActions);
        const url = `${BASE_URL}${action.path}`;

        const result = await makeRequest(url, action.method);
        result.userId = userId;
        result.timestamp = Date.now();
        results.push(result);

        await delay(getRandomInt(action.delay * 0.5, action.delay * 1.5));
    }

    return results;
}

function getSystemMetrics() {
    return {
        timestamp: Date.now(),
        cpu: os.cpus().map(c => ({
            model: c.model,
            speed: c.speed,
            usage: c.times.user / (c.times.user + c.times.idle) * 100
        })),
        memory: {
            total: os.totalmem(),
            free: os.freemem(),
            used: os.totalmem() - os.freemem(),
            percentage: ((os.totalmem() - os.freemem()) / os.totalmem() * 100)
        },
        uptime: os.uptime()
    };
}

async function runLoadTest() {
    console.log(`\n=== LexPrime Load Test ===`);
    console.log(`Base URL: ${BASE_URL}`);
    console.log(`Duration: ${TEST_DURATION} seconds`);
    console.log(`Concurrent Users: ${CONCURRENT_USERS}`);
    console.log(`Start Time: ${new Date().toISOString()}`);
    console.log(`============================\n`);

    const metrics = [];
    const metricsInterval = setInterval(() => {
        metrics.push(getSystemMetrics());
    }, 5000);

    const userPromises = [];
    for (let i = 0; i < CONCURRENT_USERS; i++) {
        userPromises.push(simulateUser(i));
    }

    const allResults = await Promise.all(userPromises);
    clearInterval(metricsInterval);

    const flatResults = allResults.flat();

    const successCount = flatResults.filter(r => r.status >= 200 && r.status < 300).length;
    const errorCount = flatResults.filter(r => r.status === 0).length;
    const failureCount = flatResults.filter(r => r.status >= 400 && r.status !== 0).length;
    
    const durations = flatResults.filter(r => r.duration).map(r => r.duration);
    const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length || 0;
    const maxDuration = Math.max(...durations, 0);
    const minDuration = Math.min(...durations.filter(d => d > 0), Infinity) || 0;
    
    const p95 = durations.sort((a, b) => a - b)[Math.floor(durations.length * 0.95)] || 0;
    const p99 = durations.sort((a, b) => a - b)[Math.floor(durations.length * 0.99)] || 0;

    const report = {
        timestamp: new Date().toISOString(),
        baseUrl: BASE_URL,
        duration: TEST_DURATION,
        concurrentUsers: CONCURRENT_USERS,
        totalRequests: flatResults.length,
        successCount,
        errorCount,
        failureCount,
        successRate: (successCount / flatResults.length * 100).toFixed(2),
        latency: {
            avg: avgDuration.toFixed(2),
            min: minDuration.toFixed(2),
            max: maxDuration.toFixed(2),
            p95: p95.toFixed(2),
            p99: p99.toFixed(2)
        },
        throughput: {
            requestsPerSecond: (flatResults.length / TEST_DURATION).toFixed(2)
        },
        systemMetrics: metrics,
        requestDetails: flatResults.slice(0, 100)
    };

    const reportPath = path.join(OUTPUT_DIR, `load-test-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log(`\n=== Load Test Results ===`);
    console.log(`Total Requests: ${report.totalRequests}`);
    console.log(`Successful: ${report.successCount} (${report.successRate}%)`);
    console.log(`Errors: ${report.errorCount}`);
    console.log(`Failures: ${report.failureCount}`);
    console.log(`\nLatency (ms):`);
    console.log(`  Average: ${report.latency.avg}`);
    console.log(`  Minimum: ${report.latency.min}`);
    console.log(`  Maximum: ${report.latency.max}`);
    console.log(`  P95: ${report.latency.p95}`);
    console.log(`  P99: ${report.latency.p99}`);
    console.log(`\nThroughput:`);
    console.log(`  Requests/sec: ${report.throughput.requestsPerSecond}`);
    console.log(`\nReport saved to: ${reportPath}`);
    console.log(`\n============================\n`);

    return report;
}

if (require.main === module) {
    runLoadTest().catch(console.error);
}

module.exports = { runLoadTest };