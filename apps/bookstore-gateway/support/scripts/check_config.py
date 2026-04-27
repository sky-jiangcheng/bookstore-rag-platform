#!/usr/bin/env python3
"""
配置检查脚本

用于在服务启动前验证配置文件的完整性和一致性，确保所有配置都是正确的，没有冲突。

Usage:
    python check_config.py [--env ENVIRONMENT]

Example:
    python check_config.py --env production
"""
import argparse
import logging
from app.utils.config_validator import config_validator
from app.utils.config_loader import config_loader

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_config(env=None):
    """检查配置文件

    Args:
        env: 环境名称

    Returns:
        bool: 配置是否有效
    """
    logger.info("开始配置检查...")

    # 验证配置完整性
    logger.info("验证配置完整性...")
    if not config_validator.validate_config():
        logger.error("配置完整性检查失败")
        return False

    # 验证配置一致性
    logger.info("验证配置一致性...")
    if not config_validator.check_config_consistency():
        logger.error("配置一致性检查失败")
        return False

    # 验证当前环境配置
    if env:
        logger.info(f"验证 {env} 环境配置...")
        try:
            # 临时修改环境变量进行验证
            import os
            original_env = os.getenv("APP_ENV")
            os.environ["APP_ENV"] = env
            
            # 重新加载配置
            from app.utils.config_loader import ConfigLoader
            new_config_loader = ConfigLoader()
            new_config_loader.load_config()
            
            # 恢复原始环境变量
            if original_env:
                os.environ["APP_ENV"] = original_env
            else:
                del os.environ["APP_ENV"]
            
            logger.info(f"{env} 环境配置验证通过")
        except Exception as e:
            logger.error(f"{env} 环境配置验证失败: {str(e)}")
            return False

    logger.info("配置检查完成，所有检查通过！")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="配置检查脚本")
    parser.add_argument("--env", type=str, default=None, help="环境名称")
    args = parser.parse_args()

    if check_config(args.env):
        logger.info("配置检查通过，可以启动服务")
        exit(0)
    else:
        logger.error("配置检查失败，请修复配置问题后再启动服务")
        exit(1)
