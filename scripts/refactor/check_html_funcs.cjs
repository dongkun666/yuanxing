const fs = require('fs');
const c = fs.readFileSync('E:/元枢法智前端/yuanxing/templates/views/knowledge.html', 'utf-8');
const re = /sortKnowledgeTable|triggerKnowledgeSearch|switchKnowledgeMainTab/g;
const m = [...c.matchAll(re)];
console.log('matches:', m.length);
m.slice(0, 20).forEach(x => console.log(' -', x[0], 'at pos', x.index));
