'use strict';

var fs = require('fs');
var path = require('path');
var DataGenerator = require('./data-generator.js');

function importCases(count, outputPath) {
    count = count || 100;
    outputPath = outputPath || path.join(__dirname, 'output', 'cases.json');

    var cases = DataGenerator.generateCases(count);

    var outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(cases, null, 2), 'utf-8');

    console.log('已生成 ' + cases.length + ' 条判例数据，保存至: ' + outputPath);
    return cases;
}

if (require.main === module) {
    var args = process.argv.slice(2);
    var count = parseInt(args[0], 10) || 100;
    var output = args[1];

    importCases(count, output);
}

module.exports = { importCases: importCases };
