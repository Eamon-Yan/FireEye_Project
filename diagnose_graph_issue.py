#!/usr/bin/env python3
"""
图表可视化问题诊断脚本 / Graph Visualization Issue Diagnostic Script

使用方法 / Usage:
    python diagnose_graph_issue.py
"""

import subprocess
import json
import sys
from typing import Dict, Any, Tuple

class Colors:
    """ANSI 颜色代码"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def run_command(cmd: str, shell: bool = True) -> Tuple[bool, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "命令执行超时"
    except Exception as e:
        return False, str(e)

def check_docker_containers() -> Dict[str, bool]:
    """检查 Docker 容器状态"""
    print_header("1. 检查 Docker 容器状态 / Checking Docker Containers")
    
    containers = {
        'fire-eye-neo4j': 'Neo4j 数据库',
        'fire-eye-redis': 'Redis 缓存',
        'fire-eye-backend': '后端 API',
        'fire-eye-frontend': '前端应用'
    }
    
    results = {}
    
    for container_name, description in containers.items():
        success, output = run_command(f"docker ps --filter name={container_name} --format '{{{{.Status}}}}'")
        
        if success and output.strip():
            status = output.strip()
            if 'Up' in status:
                print_success(f"{description} ({container_name}): {status}")
                results[container_name] = True
            else:
                print_error(f"{description} ({container_name}): {status}")
                results[container_name] = False
        else:
            print_error(f"{description} ({container_name}): 未运行")
            results[container_name] = False
    
    return results

def check_neo4j_connection() -> bool:
    """检查 Neo4j 连接"""
    print_header("2. 检查 Neo4j 连接 / Checking Neo4j Connection")
    
    cmd = """docker exec fire-eye-neo4j cypher-shell -u neo4j -p password "RETURN 'Neo4j is working' as message;" 2>&1"""
    success, output = run_command(cmd)
    
    if success and 'working' in output:
        print_success("Neo4j 连接成功")
        return True
    else:
        print_error("Neo4j 连接失败")
        print_info(f"输出: {output[:200]}")
        return False

def check_neo4j_data() -> Tuple[int, int]:
    """检查 Neo4j 中的数据"""
    print_header("3. 检查 Neo4j 数据 / Checking Neo4j Data")
    
    # 获取节点数
    cmd_nodes = """docker exec fire-eye-neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n) as count;" 2>&1 | grep -oP '\\d+' | head -1"""
    success_nodes, output_nodes = run_command(cmd_nodes)
    
    node_count = 0
    if success_nodes and output_nodes.strip():
        try:
            node_count = int(output_nodes.strip())
        except:
            pass
    
    # 获取关系数
    cmd_rels = """docker exec fire-eye-neo4j cypher-shell -u neo4j -p password "MATCH ()-[r]->() RETURN count(r) as count;" 2>&1 | grep -oP '\\d+' | head -1"""
    success_rels, output_rels = run_command(cmd_rels)
    
    rel_count = 0
    if success_rels and output_rels.strip():
        try:
            rel_count = int(output_rels.strip())
        except:
            pass
    
    print_info(f"节点数: {node_count}")
    print_info(f"关系数: {rel_count}")
    
    if node_count == 0:
        print_warning("数据库为空 - 需要上传文件来填充数据")
    else:
        print_success(f"数据库中有数据: {node_count} 个节点, {rel_count} 个关系")
    
    return node_count, rel_count

def check_backend_health() -> bool:
    """检查后端健康状态"""
    print_header("4. 检查后端健康状态 / Checking Backend Health")
    
    cmd = "curl -s -X GET http://localhost:8000/api/v1/graph/health"
    success, output = run_command(cmd)
    
    if success:
        try:
            data = json.loads(output)
            if data.get('status') == 'success':
                print_success("后端健康检查通过")
                return True
        except:
            pass
    
    print_error("后端健康检查失败")
    print_info(f"输出: {output[:200]}")
    return False

def check_graph_query() -> Tuple[int, int]:
    """检查图表查询端点"""
    print_header("5. 检查图表查询端点 / Checking Graph Query Endpoint")
    
    cmd = "curl -s -X GET 'http://localhost:8000/api/v1/graph/query?limit=100&include_relationships=true'"
    success, output = run_command(cmd)
    
    if success:
        try:
            data = json.loads(output)
            if data.get('status') == 'success':
                nodes = data.get('data', {}).get('nodes', [])
                links = data.get('data', {}).get('links', [])
                
                print_success(f"查询成功: {len(nodes)} 个节点, {len(links)} 个关系")
                
                if len(nodes) == 0:
                    print_warning("查询返回空结果 - 数据库可能为空")
                
                return len(nodes), len(links)
        except Exception as e:
            print_error(f"解析响应失败: {e}")
    else:
        print_error("查询失败")
        print_info(f"输出: {output[:200]}")
    
    return 0, 0

def check_frontend_config() -> bool:
    """检查前端配置"""
    print_header("6. 检查前端配置 / Checking Frontend Configuration")
    
    cmd = "cat fire-eye-system/frontend/.env.local 2>/dev/null || echo '文件不存在'"
    success, output = run_command(cmd)
    
    if 'NEXT_PUBLIC_API_URL' in output:
        print_success("前端环境变量配置正确")
        print_info(f"API URL: {[line for line in output.split('\\n') if 'NEXT_PUBLIC_API_URL' in line]}")
        return True
    else:
        print_warning("前端环境变量可能未配置")
        return False

def check_backend_logs() -> None:
    """检查后端日志"""
    print_header("7. 检查后端日志 / Checking Backend Logs")
    
    cmd = "docker logs fire-eye-backend --tail 20 2>&1 | tail -10"
    success, output = run_command(cmd)
    
    if success and output.strip():
        print_info("最近的后端日志:")
        for line in output.strip().split('\n')[-5:]:
            if 'error' in line.lower() or 'exception' in line.lower():
                print_error(f"  {line}")
            else:
                print_info(f"  {line}")
    else:
        print_warning("无法获取后端日志")

def print_recommendations(node_count: int, rel_count: int, backend_ok: bool) -> None:
    """打印建议"""
    print_header("建议 / Recommendations")
    
    if node_count == 0:
        print_warning("数据库为空")
        print_info("解决方案:")
        print_info("  1. 打开上传页面: http://localhost:3000/upload")
        print_info("  2. 选择测试文件: fire-eye-system/测试文档-火灾调查报告示例.txt")
        print_info("  3. 点击上传按钮")
        print_info("  4. 等待分析完成 (30-60 秒)")
        print_info("  5. 刷新图表页面: http://localhost:3000/graph")
    elif not backend_ok:
        print_error("后端连接有问题")
        print_info("解决方案:")
        print_info("  1. 重启后端: docker restart fire-eye-backend")
        print_info("  2. 等待 30 秒")
        print_info("  3. 重新运行此诊断脚本")
    else:
        print_success("系统状态正常")
        print_info("如果仍然看不到节点:")
        print_info("  1. 刷新浏览器页面 (Ctrl+F5)")
        print_info("  2. 检查浏览器控制台 (F12)")
        print_info("  3. 查看网络请求是否成功")

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}火瞳系统 - 图表可视化问题诊断{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}Fire-Eye System - Graph Visualization Diagnostic{Colors.RESET}\n")
    
    # 检查 Docker
    containers = check_docker_containers()
    
    if not all(containers.values()):
        print_error("某些容器未运行，请先启动系统:")
        print_info("  docker-compose up -d")
        sys.exit(1)
    
    # 检查 Neo4j
    neo4j_ok = check_neo4j_connection()
    if not neo4j_ok:
        print_error("Neo4j 连接失败，请检查容器日志")
        sys.exit(1)
    
    # 获取数据统计
    node_count, rel_count = check_neo4j_data()
    
    # 检查后端
    backend_ok = check_backend_health()
    
    # 检查查询端点
    query_nodes, query_links = check_graph_query()
    
    # 检查前端配置
    check_frontend_config()
    
    # 检查日志
    check_backend_logs()
    
    # 打印建议
    print_recommendations(node_count, rel_count, backend_ok)
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}诊断完成 / Diagnostic Complete{Colors.RESET}\n")

if __name__ == '__main__':
    main()
