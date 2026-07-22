'use strict';

var fs = require('fs');
var path = require('path');
var DataGenerator = require('./data-generator.js');

function importLawyers(count, outputPath) {
    count = count || 30;
    outputPath = outputPath || path.join(__dirname, 'output', 'lawyers.json');

    var lawyers = DataGenerator.generateLawyers(count);

    var outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(lawyers, null, 2), 'utf-8');

    console.log('已生成 ' + lawyers.length + ' 条律师数据，保存至: ' + outputPath);
    return lawyers;
}

if (require.main === module) {
    var args = process.argv.slice(2);
    var count = parseInt(args[0], 10) || 30;
    var output = args[1];

    importLawyers(count, output);
}

module.exports = { importLawyers: importLawyers };
