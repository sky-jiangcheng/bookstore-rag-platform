"""
数据库迁移脚本：为 t_book_info 表添加筛选相关字段

运行方式：
    python migrations/add_filter_fields.py
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from app.utils.database import engine, get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """执行数据库迁移"""
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()

            try:
                # 检查字段是否已存在
                check_sql = """
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 't_book_info'
                    AND COLUMN_NAME IN ('filter_tags', 'matched_keywords')
                """
                result = conn.execute(text(check_sql))
                existing_columns = [row[0] for row in result]

                # 添加 filter_tags 字段
                if 'filter_tags' not in existing_columns:
                    logger.info("添加 filter_tags 字段...")
                    conn.execute(text("""
                        ALTER TABLE t_book_info
                        ADD COLUMN filter_tags JSON NULL
                        COMMENT '筛选标签分类'
                    """))
                    logger.info("filter_tags 字段添加成功")
                else:
                    logger.info("filter_tags 字段已存在，跳过")

                # 添加 matched_keywords 字段
                if 'matched_keywords' not in existing_columns:
                    logger.info("添加 matched_keywords 字段...")
                    conn.execute(text("""
                        ALTER TABLE t_book_info
                        ADD COLUMN matched_keywords JSON NULL
                        COMMENT '匹配到的筛选关键词'
                    """))
                    logger.info("matched_keywords 字段添加成功")
                else:
                    logger.info("matched_keywords 字段已存在，跳过")

                # 提交事务
                trans.commit()
                logger.info("数据库迁移完成！")

            except Exception as e:
                # 回滚事务
                trans.rollback()
                logger.error(f"迁移过程中发生错误，已回滚: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info("开始数据库迁移...")
    migrate()
    logger.info("迁移脚本执行完毕")
