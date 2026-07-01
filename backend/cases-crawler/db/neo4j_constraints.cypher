// LexPrime Neo4j 图数据库约束 (股权穿透 + 案件关系)
// 2026-06-28
// 执行: cypher-shell -u neo4j -p pwd < db/neo4j_constraints.cypher

// ===== 节点唯一性约束 =====
CREATE CONSTRAINT company_unified_id IF NOT EXISTS
FOR (c:Company) REQUIRE c.unified_id IS UNIQUE;

CREATE CONSTRAINT lawyer_id IF NOT EXISTS
FOR (l:Lawyer) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT firm_id IF NOT EXISTS
FOR (f:Firm) REQUIRE f.id IS UNIQUE;

CREATE CONSTRAINT case_doc_id IF NOT EXISTS
FOR (c:Case) REQUIRE c.doc_id IS UNIQUE;

CREATE CONSTRAINT law_id IF NOT EXISTS
FOR (l:Law) REQUIRE l.law_id IS UNIQUE;

CREATE CONSTRAINT person_id IF NOT EXISTS
FOR (p:Person) REQUIRE p.id IS UNIQUE;

// ===== 索引 (加速查询) =====
CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON (c.name);
CREATE INDEX lawyer_name IF NOT EXISTS FOR (l:Lawyer) ON (l.name);
CREATE INDEX case_cause IF NOT EXISTS FOR (c:Case) ON (c.cause);
CREATE INDEX law_title IF NOT EXISTS FOR (l:Law) ON (l.title);

// ===== 关系说明 (创建时显式定义) =====
// (:Company)-[:OWNS {ratio, amount, since}]->(:Company)  股权
// (:Person)-[:CONTROLS]->(:Company)  控制
// (:Company)-[:IS_LAWYER_OF]->(:Lawyer)  法人/股东
// (:Case)-[:CITES]->(:Law)  判例引用法条
// (:Case)-[:SIMILAR_TO {score}]->(:Case)  类案关系
// (:Lawyer)-[:WORKS_AT {role, since}]->(:Firm)  律师就职
// (:Lawyer)-[:HANDLES {role}]->(:Case)  律师办案

// ===== 股权穿透示例 (插入测试数据后可用) =====
// MATCH (c:Company {unified_id: "91110000XXXXXXXXX"})
// OPTIONAL MATCH path = (c)-[:OWNS*1..5]->(subsidiaries:Company)
// RETURN c, subsidiaries, path
