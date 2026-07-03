'use strict';

var fs = require('fs');
var path = require('path');
var DataGenerator = require('./data-generator.js');

function importLaws(count, outputPath) {
    count = count || 50;
    outputPath = outputPath || path.join(__dirname, 'output', 'laws.json');

    var laws = DataGenerator.generateLaws(count);

    var outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, JSON.stringify(laws, null, 2), 'utf-8');

    console.log('已生成 ' + laws.length + ' 条法规数据，保存至: ' + outputPath);
    return laws;
}

if (require.main === module) {
    var args = process.argv.slice(2);
    var count = parseInt(args[0], 10) || 50;
    var output = args[1];

    importLaws(count, output);
}

module.exports = { importLaws: importLaws };
