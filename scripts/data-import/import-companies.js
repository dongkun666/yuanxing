'use strict';

var fs = require('fs');
var path = require('path');
var DataGenerator = require('./data-generator.js');

function importCompanies(count, outputPath) {
    count = count || 50;
    outputPath = outputPath || path.join(__dirname, 'output', 'companies.json');

    var companies = DataGenerator.generateCompanies(count);

    var outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(companies, null, 2), 'utf-8');

    console.log('已生成 ' + companies.length + ' 条企业数据，保存至: ' + outputPath);
    return companies;
}

if (require.main === module) {
    var args = process.argv.slice(2);
    var count = parseInt(args[0], 10) || 50;
    var output = args[1];

    importCompanies(count, output);
}

module.exports = { importCompanies: importCompanies };
