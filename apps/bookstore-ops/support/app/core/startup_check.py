"""
启动前检查机制

在应用启动时执行的检查，确保系统各组件正常运行
"""
import logging
import os
import sys
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class StartupCheck:
    """启动检查类"""
    
    def __init__(self):
        """初始化启动检查"""
        # 固定到 backend 目录，避免依赖当前工作目录
        self.base_dir = Path(__file__).resolve().parents[2]
        self.checks = []
        self._register_checks()
    
    def _register_checks(self):
        """注册检查项"""
        self.checks = [
            {
                "name": "目录结构检查",
                "function": self._check_directory_structure,
                "critical": True
            },
            {
                "name": "配置文件检查",
                "function": self._check_config_files,
                "critical": True
            },
            {
                "name": "环境变量检查",
                "function": self._check_environment_variables,
                "critical": False
            },
            {
                "name": "认证配置检查",
                "function": self._check_auth_config,
                "critical": False
            },
            {
                "name": "API 路由检查",
                "function": self._check_api_routes,
                "critical": False
            },
        ]
    
    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有检查
        
        Returns:
            检查结果字典
        """
        results = {
            "success": True,
            "checks": []
        }
        
        logger.info("开始执行启动前检查...")
        
        for check in self.checks:
            check_name = check["name"]
            check_func = check["function"]
            critical = check["critical"]
            
            try:
                check_result = check_func()
                results["checks"].append({
                    "name": check_name,
                    "success": True,
                    "message": check_result
                })
                logger.info(f"✅ {check_name}: {check_result}")
            except Exception as e:
                error_message = str(e)
                results["checks"].append({
                    "name": check_name,
                    "success": False,
                    "message": error_message
                })
                logger.error(f"❌ {check_name}: {error_message}")
                
                if critical:
                    results["success"] = False
        
        if results["success"]:
            logger.info("启动前检查全部通过！")
        else:
            logger.error("启动前检查失败，请修复相关问题后再启动应用")
        
        return results
    
    def _check_directory_structure(self) -> str:
        """检查目录结构
        
        Returns:
            检查结果消息
        """
        required_dirs = [
            "logs",
            "models",
            "config"
        ]
        
        for dir_name in required_dirs:
            dir_path = self.base_dir / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {dir_name}")
        
        return "目录结构检查通过"
    
    def _check_config_files(self) -> str:
        """检查配置文件
        
        Returns:
            检查结果消息
        """
        config_files = [
            self.base_dir / "config" / "config.yml"
        ]
        
        for config_file in config_files:
            if not Path(config_file).exists():
                raise Exception(f"配置文件不存在: {config_file}")
        
        return "配置文件检查通过"
    
    def _check_environment_variables(self) -> str:
        """检查环境变量
        
        Returns:
            检查结果消息
        """
        # 检查 .env 文件是否存在
        if os.path.exists(".env"):
            logger.info(".env 文件存在")
        else:
            logger.warning(".env 文件不存在，将使用默认配置")
        
        return "环境变量检查完成"
    
    def _check_auth_config(self) -> str:
        """检查认证配置
        
        Returns:
            检查结果消息
        """
        # 检查认证相关配置
        # 这里可以添加更详细的认证配置检查逻辑
        # 例如检查JWT密钥长度、认证路由是否存在等
        
        # 记录登录获取token的准则
        logger.info("📝 认证准则: 所有API端点都需要认证，必须先登录获取token再调用接口")
        logger.info("📝 验证流程: 1. 调用登录接口获取token 2. 在请求头中添加Authorization: Bearer <token>")
        
        return "认证配置检查完成，已记录登录获取token的准则"
    
    def _check_frontend_build(self) -> str:
        """检查前端编译
        
        Returns:
            检查结果消息
        """
        import os
        import subprocess
        
        # 检查前端目录是否存在
        # 从startup_check.py文件路径向上四级找到项目根目录，然后进入frontend目录
        current_file = os.path.abspath(__file__)
        # 路径：backend/app/core/startup_check.py -> 向上四级到项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
        frontend_dir = os.path.join(project_root, "frontend")
        
        if not os.path.exists(frontend_dir):
            logger.warning(f"前端目录不存在: {frontend_dir}，跳过前端编译检查")
            return "前端目录不存在，跳过前端编译检查"
        
        # 检查是否有 package.json 文件
        package_json = os.path.join(frontend_dir, "package.json")
        if not os.path.exists(package_json):
            logger.warning("前端 package.json 文件不存在，跳过前端编译检查")
            return "前端 package.json 文件不存在，跳过前端编译检查"
        
        # 尝试运行前端构建命令
        logger.info("开始检查前端编译...")
        
        try:
            # 运行 npm run build 命令
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                logger.info("✅ 前端编译检查通过")
                return "前端编译检查通过"
            else:
                error_message = f"前端编译失败: {result.stderr[:500]}..."
                logger.error(f"❌ 前端编译检查失败: {error_message}")
                raise Exception(error_message)
                
        except subprocess.TimeoutExpired:
            error_message = "前端编译超时（超过5分钟）"
            logger.error(f"❌ 前端编译检查失败: {error_message}")
            raise Exception(error_message)
        except Exception as e:
            error_message = f"前端编译检查出错: {str(e)}"
            logger.error(f"❌ 前端编译检查失败: {error_message}")
            raise Exception(error_message)
    
    def _check_api_routes(self) -> str:
        """检查 API 路由
        
        Returns:
            检查结果消息
        """
        # 这里可以添加更详细的路由检查逻辑
        # 例如检查前端代码中的 API 路径是否与后端一致
        return "API 路由检查完成"


def run_startup_checks() -> bool:
    """运行启动检查
    
    Returns:
        是否所有检查都通过
    """
    checker = StartupCheck()
    results = checker.run_all_checks()
    return results["success"]


if __name__ == "__main__":
    """单独运行启动检查"""
    success = run_startup_checks()
    sys.exit(0 if success else 1)
