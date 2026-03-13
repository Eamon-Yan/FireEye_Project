import asyncio
from app.db.neo4j_manager import neo4j_manager

async def test_search():
    await neo4j_manager.connect()
    
    # 测试1: 获取所有节点
    print("=== 测试1: 获取所有节点 ===")
    results = await neo4j_manager.execute_query("MATCH (n) RETURN n, labels(n) as labels LIMIT 3")
    for r in results:
        print(f"Node: {r['n']}")
        print(f"Labels: {r['labels']}")
        print()
    
    # 测试2: 测试搜索
    print("=== 测试2: 测试搜索 ===")
    query = """
    MATCH (n)
    WHERE toLower(toString(n.description)) CONTAINS toLower($search_text)
       OR toLower(toString(n.standard_term)) CONTAINS toLower($search_text)
       OR toLower(toString(n.name)) CONTAINS toLower($search_text)
       OR toLower(toString(n.id)) CONTAINS toLower($search_text)
    RETURN n, labels(n) as labels
    LIMIT 5
    """
    results = await neo4j_manager.execute_query(query, {"search_text": "fire"})
    print(f"Found {len(results)} results for 'fire'")
    for r in results:
        print(f"Node: {r['n']}")
        print()
    
    # 测试3: 测试中文搜索
    print("=== 测试3: 测试中文搜索 ===")
    results = await neo4j_manager.execute_query(query, {"search_text": "火"})
    print(f"Found {len(results)} results for '火'")
    for r in results:
        print(f"Node: {r['n']}")
        print()

if __name__ == "__main__":
    asyncio.run(test_search())
