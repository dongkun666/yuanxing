const fs = require('fs');
const c = fs.readFileSync('E:/元枢法智前端/yuanxing/templates/views/knowledge.html', 'utf-8');
const m = [...c.matchAll(/id="kb-search-input"/g)];
console.log('kb-search-input count:', m.length);
const re2 = /switchKnowledgeTab|sortKnowledgeTable|triggerKnowledgeSearch/g;
const m2 = [...c.matchAll(re2)];
console.log('orphan funcs in HTML:', m2.length);
