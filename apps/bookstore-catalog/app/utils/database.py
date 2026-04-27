from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.utils.config_loader import config_loader

# 从配置加载器获取数据库URL
DATABASE_URL = config_loader.get_database_url()

def _create_engine(database_url: str):
    """根据数据库类型创建引擎。"""
    engine_kwargs = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "echo": False,
    }

    if database_url.startswith("sqlite:"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20

    return create_engine(database_url, **engine_kwargs)


# 配置数据库连接池
engine = _create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
