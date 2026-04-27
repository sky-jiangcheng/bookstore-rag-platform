import asyncio
import inspect
import json
import os
from types import SimpleNamespace

import httpx
import pytest
from pathlib import Path
import sys

# 让测试环境默认进入降级认证模式，避免每个用例都要先登录取 token。
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("BOOKSTORE_DEGRADED_AUTH", "1")

backend_root = Path(__file__).resolve().parents[1]
backend_root_str = str(backend_root)
if backend_root_str not in sys.path:
    sys.path.insert(0, backend_root_str)

from app.agents.requirement_agent import RequirementAgent as AppRequirementAgent
from app.agents.requirement_agent import RequirementAgent as BackendRequirementAgent
from app.agents.workflow import workflow_manager
from app.core.conversation_manager import ConversationManager
from app.core.circuit_breaker import CircuitBreaker
from main import app


def _fake_requirement_response(user_input: str) -> dict:
    text = user_input.lower()

    if "给我推荐几本书" in user_input or user_input.strip() in {"推荐书", "给我推荐书"}:
        return {
            "target_audience": {"occupation": "通用", "age_group": "成人", "reading_level": "通用"},
            "categories": [{"name": "综合", "percentage": 100}],
            "keywords": [],
            "constraints": {"budget": None, "exclude_textbooks": False, "other": []},
            "confidence": 0.35,
            "needs_clarification": True,
            "clarification_questions": ["您主要关注哪些主题？", "预算范围是多少？"],
        }

    if "python" in text:
        categories = [{"name": "Python", "percentage": 60}]
        if "算法" in text or "数据结构" in text:
            categories.append({"name": "算法", "percentage": 40})
        return {
            "target_audience": {"occupation": "学生", "age_group": "成人", "reading_level": "入门"},
            "categories": categories,
            "keywords": ["Python", "编程"],
            "constraints": {"budget": 500, "exclude_textbooks": True, "other": []},
            "confidence": 0.95,
            "needs_clarification": False,
            "clarification_questions": [],
        }

    if "算法" in user_input or "数据结构" in user_input:
        return {
            "target_audience": {"occupation": "程序员", "age_group": "成人", "reading_level": "进阶"},
            "categories": [{"name": "算法", "percentage": 60}, {"name": "数据结构", "percentage": 40}],
            "keywords": ["算法", "数据结构"],
            "constraints": {"budget": 500, "exclude_textbooks": False, "other": []},
            "confidence": 0.9,
            "needs_clarification": False,
            "clarification_questions": [],
        }

    return {
        "target_audience": {"occupation": "通用", "age_group": "成人", "reading_level": "通用"},
        "categories": [{"name": "综合", "percentage": 100}],
        "keywords": ["阅读"],
        "constraints": {"budget": 300, "exclude_textbooks": True, "other": []},
        "confidence": 0.8,
        "needs_clarification": False,
        "clarification_questions": [],
    }


async def _fake_reply(self, msg):
    content = getattr(msg, "content", "") or ""
    response = _fake_requirement_response(content)
    return SimpleNamespace(content=json.dumps(response, ensure_ascii=False))


@pytest.fixture(autouse=True)
def mock_requirement_agent(monkeypatch):
    """Make agent tests deterministic without hitting real model APIs."""
    monkeypatch.setattr(AppRequirementAgent, "reply", _fake_reply, raising=True)
    monkeypatch.setattr(BackendRequirementAgent, "reply", _fake_reply, raising=True)


@pytest.fixture(autouse=True)
def clean_workflow_manager():
    """Avoid cross-test workflow state leakage."""
    workflow_manager.workflows.clear()
    yield
    workflow_manager.workflows.clear()


@pytest.fixture
def circuit_breaker():
    return CircuitBreaker(name="test_breaker", fail_max=3, reset_timeout=1)


@pytest.fixture
def conversation_manager():
    return ConversationManager(db=object(), cache_service=None)


@pytest.fixture
def client():
    transport = httpx.ASGITransport(app=app)
    test_client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    yield test_client
    asyncio.run(test_client.aclose())


def pytest_pyfunc_call(pyfuncitem):
    """Run async test functions without requiring pytest-asyncio."""
    testfunction = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunction):
        kwargs = {name: pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames}
        asyncio.run(testfunction(**kwargs))
        return True
    return None
