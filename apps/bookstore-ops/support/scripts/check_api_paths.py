#!/usr/bin/env python3
"""
API路径检查脚本
用于检查前端的API调用路径与后端定义的路径是否一致，避免404错误
"""
import os
import re
import json
from typing import Dict, List, Set

# 项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # 从 scripts 回到项目根目录
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')
# 五个后端服务目录（顶级并列）
BACKEND_SERVICES = ['gateway', 'auth', 'catalog', 'ops', 'rag']
BACKEND_SERVICE_DIRS = [os.path.join(PROJECT_ROOT, service) for service in BACKEND_SERVICES]

# 前端API调用模式
FRONTEND_API_PATTERNS = [
    r"request\.(get|post|put|delete)\(['\"]([^'\"]+)['\"]",
    r"axios\.(get|post|put|delete)\(['\"]([^'\"]+)['\"]",
    r"fetch\(['\"]([^'\"]+)['\"]",
]

# 后端路由模式
BACKEND_ROUTE_PATTERNS = [
    r"@router\.(get|post|put|delete)\(['\"]([^'\"]+)['\"]",
]

def scan_frontend_api_calls() -> Set[str]:
    """
    扫描前端代码中的API调用路径
    """
    api_paths = set()

    # 遍历前端目录
    for root, dirs, files in os.walk(FRONTEND_DIR):
        # 跳过node_modules目录
        if 'node_modules' in dirs:
            dirs.remove('node_modules')

        for file in files:
            if file.endswith(('.js', '.vue', '.ts')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 查找API调用
                    for pattern in FRONTEND_API_PATTERNS:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, tuple) and len(match) == 2:
                                path = match[1]
                                # 移除查询参数
                                if '?' in path:
                                    path = path.split('?')[0]
                                # 标准化路径
                                path = path.strip()
                                if path and path.startswith('/'):
                                    api_paths.add(path)
                except Exception as e:
                    print(f"Error scanning {file_path}: {e}")

    return api_paths

def scan_backend_routes() -> Set[str]:
    """
    扫描后端代码中的路由定义
    """
    routes = set()

    # 遍历五个后端服务，每个服务扫描自己的API目录
    for service_name, service_dir in zip(BACKEND_SERVICES, BACKEND_SERVICE_DIRS):
        # 每个服务都有 routes.py 包含路由汇总
        routes_file = os.path.join(service_dir, 'app', 'routes.py')
        if not os.path.exists(routes_file):
            continue

        # API 目录在每个服务自己的 app/api 下
        api_dir = os.path.join(service_dir, 'app', 'api')
        if not os.path.exists(api_dir):
            continue

        try:
            with open(routes_file, 'r', encoding='utf-8') as f:
                routes_content = f.read()

            # 从 routes.py 中提取 include_router 信息: router.include_router(xxx.router, prefix="/api/v1/auth", tags=["认证"])
            # 匹配 pattern: router\.include_router\(([^,]+)\.router,\s*(?:.*prefix=["\']([^"\']+)["\'])?
            include_pattern = r'router\.include_router\(([^,]+)\.router,\s*(?:.*prefix=["\']([^"\']+)["\'])?'
            matches = re.findall(include_pattern, routes_content)

            # 构建路由前缀映射 {module_name: prefix}
            router_prefixes = {}
            for match in matches:
                module_name = match[0].strip()
                prefix = match[1].strip() if len(match) > 1 and match[1] else ''
                if prefix:
                    if not prefix.startswith('/'):
                        prefix = '/' + prefix
                    router_prefixes[module_name] = prefix
        except Exception as e:
            print(f"Error scanning {routes_file}: {e}")
            router_prefixes = {}

        # 遍历当前服务的 API 目录
        for root, dirs, files in os.walk(api_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    # 提取模块名称，如auth_management.py -> auth_management
                    module_name = os.path.splitext(file)[0]

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # 查找模块自己设置的prefix
                        module_prefix = ''
                        prefix_match = re.search(r'router = APIRouter\(.*prefix=["\']([^"\']+)["\']', content, re.DOTALL)
                        if prefix_match:
                            module_prefix = prefix_match.group(1)
                            if not module_prefix.startswith('/'):
                                module_prefix = '/' + module_prefix
                            if module_prefix.endswith('/'):
                                module_prefix = module_prefix[:-1]

                        # 获取 routes.py 中设置的路由前缀
                        main_prefix = router_prefixes.get(module_name, '')

                        # 确定最终的路由前缀
                        final_prefix = main_prefix + module_prefix

                        # 查找路由装饰器
                        for pattern in BACKEND_ROUTE_PATTERNS:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if isinstance(match, tuple) and len(match) == 2:
                                    path = match[1]
                                    # 标准化路径
                                    path = path.strip()
                                    if path and path.startswith('/'):
                                        # 组合路由前缀和路径
                                        full_path = final_prefix + path
                                        # 移除路径参数
                                        full_path = re.sub(r'\{[^\}]+\}', '', full_path)
                                        routes.add(full_path)
                    except Exception as e:
                        print(f"Error scanning {file_path}: {e}")

    return routes

def check_api_paths() -> Dict[str, List[str]]:
    """
    检查前端API调用路径与后端路由定义是否一致
    """
    print("Scanning frontend API calls...")
    frontend_paths = scan_frontend_api_calls()
    print(f"Found {len(frontend_paths)} frontend API paths")

    print("Scanning backend routes...")
    backend_paths = scan_backend_routes()
    print(f"Found {len(backend_paths)} backend routes")

    # 在 gateway 的 routes.py 中再次提取路由前缀，用于检查
    routes_file = os.path.join(PROJECT_ROOT, 'gateway', 'app', 'routes.py')
    router_prefixes = {}
    if os.path.exists(routes_file):
        try:
            with open(routes_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找app.include_router调用
            include_pattern = r'router\.include_router\(([^,]+)\.router,\s*(?:.*prefix=["\']([^"\']+)["\'])?'
            matches = re.findall(include_pattern, content)
            for match in matches:
                if len(match) >= 2:
                    router_name = match[0].strip()
                    prefix = match[1].strip() if match[1] else ''
                    # 提取router模块名称
                    router_module = router_name.split('.')[0]
                    if prefix:
                        if not prefix.startswith('/'):
                            prefix = '/' + prefix
                    router_prefixes[router_module] = prefix
        except Exception as e:
            print(f"Error scanning {routes_file}: {e}")

    # 检查前端路径是否在后端路由中
    missing_paths = []
    for path in frontend_paths:
        # 构建实际的前端调用路径（添加/api前缀）
        actual_frontend_path = '/api' + path

        # 检查是否匹配后端路由
        found = False
        for backend_path in backend_paths:
            # 移除路径参数
            backend_path_clean = re.sub(r'\{[^\}]+\}', '', backend_path)

            # 检查实际前端路径是否与后端路径匹配
            if actual_frontend_path == backend_path_clean:
                found = True
                break
            # 检查实际前端路径是否以后端路径为前缀
            elif actual_frontend_path.startswith(backend_path_clean + '/'):
                found = True
                break
            # 检查后端路径是否以实际前端路径为前缀
            elif backend_path_clean.startswith(actual_frontend_path + '/'):
                found = True
                break

        if not found:
            missing_paths.append(path)

    return {
        'frontend_paths': sorted(list(frontend_paths)),
        'backend_paths': sorted(list(backend_paths)),
        'missing_paths': sorted(missing_paths),
        'router_prefixes': router_prefixes
    }

def main():
    """
    主函数
    """
    print("API路径检查开始...")
    print("=" * 60)

    result = check_api_paths()

    print("=" * 60)
    print("检查结果:")
    print(f"前端API调用路径数: {len(result['frontend_paths'])}")
    print(f"后端路由定义数: {len(result['backend_paths'])}")
    print(f"缺失的路径数: {len(result['missing_paths'])}")

    if result['missing_paths']:
        print("\n缺失的API路径:")
        for path in result['missing_paths']:
            print(f"  - {path}")
        print("\n警告: 这些路径在后端可能不存在，可能会导致404错误！")
    else:
        print("\n所有前端API调用路径在后端都有对应的路由定义，没有发现404风险。")

    # 保存结果到临时目录，避免把运行产物留在仓库根目录
    output_dir = os.path.join(PROJECT_ROOT, 'tmp')
    os.makedirs(output_dir, exist_ok=True)
    result_file = os.path.join(output_dir, 'api_paths_check_result.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n检查结果已保存到: {result_file}")
    print("API路径检查完成！")

if __name__ == '__main__':
    main()
