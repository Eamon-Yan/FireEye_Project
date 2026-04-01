// FireEye Neo4j 数据库初始化脚本

// ===== Constraints =====
CREATE CONSTRAINT fire_event_id_unique IF NOT EXISTS FOR (n:FireEvent) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT hazard_id_unique IF NOT EXISTS FOR (n:Hazard) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT consequence_id_unique IF NOT EXISTS FOR (n:Consequence) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (n:Document) REQUIRE n.id IS UNIQUE;

// ===== Indexes =====
CREATE INDEX fire_event_type_index IF NOT EXISTS FOR (n:FireEvent) ON (n.event_type);
CREATE INDEX fire_event_category_index IF NOT EXISTS FOR (n:FireEvent) ON (n.category);
CREATE INDEX fire_event_severity_index IF NOT EXISTS FOR (n:FireEvent) ON (n.severity_level);
CREATE INDEX fire_event_standard_term_index IF NOT EXISTS FOR (n:FireEvent) ON (n.standard_term);
CREATE INDEX hazard_risk_level_index IF NOT EXISTS FOR (n:Hazard) ON (n.risk_level);
CREATE INDEX consequence_impact_level_index IF NOT EXISTS FOR (n:Consequence) ON (n.impact_level);
CREATE INDEX document_status_index IF NOT EXISTS FOR (n:Document) ON (n.processing_status);

// ===== Fulltext Indexes =====
CREATE FULLTEXT INDEX fire_event_description_fulltext IF NOT EXISTS
FOR (n:FireEvent) ON EACH [n.description, n.standard_term];

CREATE FULLTEXT INDEX hazard_description_fulltext IF NOT EXISTS
FOR (n:Hazard) ON EACH [n.description];

CREATE FULLTEXT INDEX consequence_description_fulltext IF NOT EXISTS
FOR (n:Consequence) ON EACH [n.description];

// ===== 示例数据 =====
MERGE (e1:FireEvent {id: 'event_001'})
SET e1.event_type = 'cause',
    e1.description = '电气线路老化',
    e1.standard_term = '电气线路老化',
    e1.category = '电气火灾',
    e1.severity_level = 3,
    e1.frequency = 15,
    e1.created_at = datetime(),
    e1.updated_at = datetime();

MERGE (e2:FireEvent {id: 'event_002'})
SET e2.event_type = 'process',
    e2.description = '短路打火',
    e2.standard_term = '电气短路',
    e2.category = '电气火灾',
    e2.severity_level = 4,
    e2.frequency = 12,
    e2.created_at = datetime(),
    e2.updated_at = datetime();

MERGE (e3:FireEvent {id: 'event_003'})
SET e3.event_type = 'process',
    e3.description = '可燃物起火',
    e3.standard_term = '可燃物引燃',
    e3.category = '燃烧过程',
    e3.severity_level = 5,
    e3.frequency = 8,
    e3.created_at = datetime(),
    e3.updated_at = datetime();

MERGE (e4:FireEvent {id: 'event_004'})
SET e4.event_type = 'result',
    e4.description = '火势蔓延',
    e4.standard_term = '火灾蔓延',
    e4.category = '火灾发展',
    e4.severity_level = 6,
    e4.frequency = 6,
    e4.created_at = datetime(),
    e4.updated_at = datetime();

MERGE (h1:Hazard {id: 'hazard_001'})
SET h1.description = '老旧建筑电气线路',
    h1.risk_level = 'high',
    h1.location = '居民住宅区',
    h1.created_at = datetime(),
    h1.updated_at = datetime();

MERGE (h2:Hazard {id: 'hazard_002'})
SET h2.description = '电动自行车充电设施',
    h2.risk_level = 'medium',
    h2.location = '地下车库',
    h2.created_at = datetime(),
    h2.updated_at = datetime();

MERGE (c1:Consequence {id: 'consequence_001'})
SET c1.description = '人员伤亡',
    c1.impact_level = 'severe',
    c1.affected_area = '整栋建筑',
    c1.created_at = datetime(),
    c1.updated_at = datetime();

MERGE (c2:Consequence {id: 'consequence_002'})
SET c2.description = '财产损失',
    c2.impact_level = 'major',
    c2.affected_area = '多个房间',
    c2.created_at = datetime(),
    c2.updated_at = datetime();

// ===== 关系 =====
MATCH (e1:FireEvent {id: 'event_001'}), (e2:FireEvent {id: 'event_002'})
MERGE (e1)-[r1:CAUSES]->(e2)
SET r1.id = 'event_001_causes_event_002',
    r1.relation_type = 'causes',
    r1.confidence = 0.85,
    r1.time_delay = 300,
    r1.created_at = datetime();

MATCH (e2:FireEvent {id: 'event_002'}), (e3:FireEvent {id: 'event_003'})
MERGE (e2)-[r2:CAUSES]->(e3)
SET r2.id = 'event_002_causes_event_003',
    r2.relation_type = 'causes',
    r2.confidence = 0.75,
    r2.time_delay = 120,
    r2.created_at = datetime();

MATCH (e3:FireEvent {id: 'event_003'}), (e4:FireEvent {id: 'event_004'})
MERGE (e3)-[r3:CAUSES]->(e4)
SET r3.id = 'event_003_causes_event_004',
    r3.relation_type = 'causes',
    r3.confidence = 0.90,
    r3.time_delay = 600,
    r3.created_at = datetime();

MATCH (h1:Hazard {id: 'hazard_001'}), (e1:FireEvent {id: 'event_001'})
MERGE (h1)-[r4:LEADS_TO]->(e1)
SET r4.id = 'hazard_001_leads_to_event_001',
    r4.probability = 0.65,
    r4.conditions = ['湿度较高', '线路过载'],
    r4.created_at = datetime();

MATCH (h2:Hazard {id: 'hazard_002'}), (e1:FireEvent {id: 'event_001'})
MERGE (h2)-[r5:LEADS_TO]->(e1)
SET r5.id = 'hazard_002_leads_to_event_001',
    r5.probability = 0.45,
    r5.conditions = ['充电时间过长', '设备老化'],
    r5.created_at = datetime();

MATCH (e4:FireEvent {id: 'event_004'}), (c1:Consequence {id: 'consequence_001'})
MERGE (e4)-[r6:RESULTS_IN]->(c1)
SET r6.id = 'event_004_results_in_consequence_001',
    r6.severity = 8,
    r6.likelihood = 0.70,
    r6.created_at = datetime();

MATCH (e4:FireEvent {id: 'event_004'}), (c2:Consequence {id: 'consequence_002'})
MERGE (e4)-[r7:RESULTS_IN]->(c2)
SET r7.id = 'event_004_results_in_consequence_002',
    r7.severity = 6,
    r7.likelihood = 0.85,
    r7.created_at = datetime();

// ===== 校验 =====
MATCH (n)
RETURN labels(n) as node_type, count(n) as count
ORDER BY node_type;

MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY relationship_type;
