const autocannon = require('autocannon');
const fs = require('fs');
const path = require('path');

const BASE_URL = process.env.TEST_URL || 'http://localhost:8000';
const OUTPUT_DIR = path.join(__dirname, '../test-results');

fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const testCases = [
    {
        name: 'health_check',
        url: '/api/health',
        method: 'GET',
        connections: 100,
        duration: 30
    },
    {
        name: 'cases_list',
        url: '/api/cases',
        method: 'GET',
        connections: 50,
        duration: 60
    },
    {
        name: 'laws_search',
        url: '/api/laws/search?q=contract',
        method: 'GET',
        connections: 30,
        duration: 60
    },
    {
        name: 'companies_search',
        url: '/api/companies/search?q=tech',
        method: 'GET',
        connections: 30,
        duration: 60
    },
    {
        name: 'backlog_list',
        url: '/api/backlog',
        method: 'GET',
        connections: 20,
        duration: 60
    }
];

async function runTest(testCase) {
    return new Promise((resolve) => {
        const instance = autocannon({
            url: `${BASE_URL}${testCase.url}`,
            method: testCase.method,
            connections: testCase.connections,
            duration: testCase.duration,
            timeout: 10,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        autocannon.track(instance);

        instance.on('done', (result) => {
            resolve({
                testCase,
                result
            });
        });
    });
}

async function runAllTests() {
    console.log(`\n=== LexPrime Performance Test Suite ===`);
    console.log(`Base URL: ${BASE_URL}`);
    console.log(`Start Time: ${new Date().toISOString()}`);
    console.log(`=========================================\n`);

    const results = [];

    for (const testCase of testCases) {
        console.log(`Running test: ${testCase.name}`);
        console.log(`URL: ${testCase.url}`);
        console.log(`Connections: ${testCase.connections}, Duration: ${testCase.duration}s`);
        console.log('-----------------------------------------');

        try {
            const { result } = await runTest(testCase);
            results.push({
                name: testCase.name,
                url: testCase.url,
                requestsPerSecond: result.requests.average,
                latency: {
                    min: result.latency.min,
                    max: result.latency.max,
                    average: result.latency.average,
                    p95: result.latency.p95,
                    p99: result.latency.p99
                },
                throughput: {
                    average: result.throughput.average
                },
                statusCodes: result.statusCodes,
                errors: result.errors,
                timeouts: result.timeouts
            });

            console.log(`Requests/sec: ${result.requests.average.toFixed(2)}`);
            console.log(`Latency (ms): min=${result.latency.min}, max=${result.latency.max}, avg=${result.latency.average.toFixed(2)}, p95=${result.latency.p95}, p99=${result.latency.p99}`);
            console.log(`Throughput (bytes/sec): ${result.throughput.average.toFixed(2)}`);
            console.log(`Status Codes: ${JSON.stringify(result.statusCodes)}`);
            console.log(`Errors: ${result.errors}, Timeouts: ${result.timeouts}`);
        } catch (error) {
            console.error(`Test failed: ${error.message}`);
            results.push({
                name: testCase.name,
                url: testCase.url,
                error: error.message
            });
        }

        console.log('');
    }

    const report = {
        timestamp: new Date().toISOString(),
        baseUrl: BASE_URL,
        tests: results,
        summary: {
            totalTests: results.length,
            successfulTests: results.filter(r => !r.error).length,
            failedTests: results.filter(r => r.error).length,
            avgRequestsPerSecond: results.filter(r => !r.error).reduce((sum, r) => sum + r.requestsPerSecond, 0) / results.filter(r => !r.error).length || 0,
            avgLatencyMs: results.filter(r => !r.error).reduce((sum, r) => sum + r.latency.average, 0) / results.filter(r => !r.error).length || 0
        }
    };

    const reportPath = path.join(OUTPUT_DIR, `performance-report-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    console.log(`\n=== Test Summary ===`);
    console.log(`Total Tests: ${report.summary.totalTests}`);
    console.log(`Successful: ${report.summary.successfulTests}`);
    console.log(`Failed: ${report.summary.failedTests}`);
    console.log(`Avg Requests/sec: ${report.summary.avgRequestsPerSecond.toFixed(2)}`);
    console.log(`Avg Latency: ${report.summary.avgLatencyMs.toFixed(2)}ms`);
    console.log(`Report saved to: ${reportPath}`);
    console.log(`\n=========================================\n`);

    return report;
}

if (require.main === module) {
    runAllTests().catch(console.error);
}

module.exports = { runAllTests, runTest };