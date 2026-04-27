"""
需求分析Agent优化后的单元测试
验证关键词识别、置信度计算、澄清问题生成等功能
"""

import pytest
import asyncio
from app.agents.requirement_agent import RequirementAgent
from app.api.demand_analysis import validate_constraints, Constraints


class TestRequirementAgentOptimized:
    """测试优化后的需求分析Agent"""

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        return RequirementAgent()

    @pytest.mark.asyncio
    async def test_programmer_recognition(self, agent):
        """测试程序员职业识别"""
        test_cases = [
            "我想为程序员推荐一些编程书",
            "适合开发者的技术书籍",
            "程序员想进阶学什么",
        ]

        for text in test_cases:
            result = await agent.analyze(text)

            # 验证职业识别
            assert result.target_audience["occupation"] == "程序员", \
                f"未能识别程序员职业: {text}"

            # 验证至少有一个分类
            assert len(result.categories) > 0, f"未生成分类: {text}"

            # 验证置信度
            assert result.confidence >= 0.5, f"置信度过低: {result.confidence}"

    @pytest.mark.asyncio
    async def test_college_student_recognition(self, agent):
        """测试大学生识别"""
        test_cases = [
            "给大学生推荐一些编程入门书",
            "本科生学习算法的书籍",
            "适合研究生的人工智能教材",
        ]

        for text in test_cases:
            result = await agent.analyze(text)

            # 验证职业识别
            assert result.target_audience["occupation"] == "大学生", \
                f"未能识别大学生: {text}"

            # 验证阅读水平识别
            if "入门" in text:
                assert result.target_audience["reading_level"] == "入门", \
                    f"未识别入门水平: {text}"

    @pytest.mark.asyncio
    async def test_category_recognition(self, agent):
        """测试书籍分类识别"""
        test_cases = [
            ("推荐Python和Java的编程书", ["编程"]),
            ("想看历史和传记", ["历史", "传记"]),
            ("人工智能和机器学习书籍", ["人工智能"]),
            ("UI设计和产品设计", ["设计", "产品"]),
        ]

        for text, expected_categories in test_cases:
            result = await agent.analyze(text)

            # 提取实际的分类名称
            actual_categories = [cat["name"] for cat in result.categories]

            # 验证至少包含一个期望的分类
            found = any(cat in actual_categories for cat in expected_categories)
            assert found, f"未识别到期望的分类 {expected_categories}, 实际: {actual_categories}"

    @pytest.mark.asyncio
    async def test_constraint_extraction(self, agent):
        """测试约束条件提取"""
        test_cases = [
            ("预算500元的编程书", 500.0),
            ("不超过1000元的书单", 1000.0),
            ("预算大约2000", 2000.0),
        ]

        for text, expected_budget in test_cases:
            result = await agent.analyze(text)

            # 验证预算提取
            assert result.constraints["budget"] == expected_budget, \
                f"预算提取错误: 期望 {expected_budget}, 实际 {result.constraints['budget']}"

    @pytest.mark.asyncio
    async def test_low_confidence_clarification(self, agent):
        """测试低置信度时的澄清问题"""
        # 使用模糊的输入
        text = "推荐几本书"
        result = await agent.analyze(text)

        # 验证需要澄清
        assert result.needs_clarification, "应该需要澄清"

        # 验证置信度较低
        assert result.confidence < 0.5, f"置信度应该较低: {result.confidence}"

        # 验证有澄清问题
        assert len(result.clarification_questions) > 0, "应该生成澄清问题"

        # 验证澄清问题的质量（不应该包含"通用"、"综合"等词）
        for question in result.clarification_questions:
            assert "通用" not in question, f"澄清问题包含通用文案: {question}"
            assert "综合" not in question, f"澄清问题包含通用文案: {question}"

    @pytest.mark.asyncio
    async def test_no_fallback_categories(self, agent):
        """测试不生成兜底分类"""
        # 完全不相关的输入
        text = "今天天气不错"
        result = await agent.analyze(text)

        # 验证不应该有"综合"或"通用"这样的兜底分类
        category_names = [cat["name"] for cat in result.categories]
        assert "综合" not in category_names, "不应该生成'综合'兜底分类"
        assert "通用" not in category_names, "不应该生成'通用'兜底分类"

        # 验证需要澄清
        assert result.needs_clarification, "模糊输入应该需要澄清"


class TestConstraintsValidation:
    """测试硬约束验证"""

    def test_valid_constraints(self):
        """测试有效的约束条件"""
        constraints = Constraints(
            proportion_error_range=5.0,
            total_book_count=20,
            budget=500.0,
            language_preference="cn"
        )

        is_valid, error_msg = validate_constraints(constraints)
        assert is_valid, f"有效约束被拒绝: {error_msg}"

    def test_invalid_proportion_range(self):
        """测试无效的比例误差范围"""
        test_cases = [
            -1.0,  # 负数
            25.0,  # 超过20
        ]

        for value in test_cases:
            constraints = Constraints(
                proportion_error_range=value,
                total_book_count=20
            )

            is_valid, error_msg = validate_constraints(constraints)
            assert not is_valid, f"应该拒绝无效的比例误差范围: {value}"
            assert "比例误差范围" in error_msg

    def test_invalid_book_count(self):
        """测试无效的书籍总数"""
        test_cases = [
            3,   # 少于5
            150, # 多于100
        ]

        for value in test_cases:
            constraints = Constraints(
                proportion_error_range=5.0,
                total_book_count=value
            )

            is_valid, error_msg = validate_constraints(constraints)
            assert not is_valid, f"应该拒绝无效的书籍总数: {value}"
            assert "书单总数" in error_msg

    def test_invalid_budget(self):
        """测试无效的预算"""
        constraints = Constraints(
            proportion_error_range=5.0,
            total_book_count=20,
            budget=-100.0
        )

        is_valid, error_msg = validate_constraints(constraints)
        assert not is_valid, "应该拒绝负数预算"
        assert "预算" in error_msg

    def test_invalid_language_preference(self):
        """测试无效的语言偏好"""
        constraints = Constraints(
            proportion_error_range=5.0,
            total_book_count=20,
            language_preference="fr"  # 不支持的语言
        )

        is_valid, error_msg = validate_constraints(constraints)
        assert not is_valid, "应该拒绝无效的语言偏好"
        assert "语言偏好" in error_msg


class TestKeywordCoverage:
    """测试关键词覆盖度"""

    @pytest.mark.asyncio
    async def test_occupation_coverage(self):
        """测试职业关键词覆盖"""
        agent = RequirementAgent()

        # 测试各种职业关键词
        occupation_tests = [
            ("产品经理想看什么书", "产品经理"),
            ("设计师推荐书籍", "设计师"),
            ("教师适合读什么", "教师"),
            ("数据分析师的学习资料", "数据分析师"),
        ]

        for text, expected_occupation in occupation_tests:
            result = await agent.analyze(text)
            actual = result.target_audience.get("occupation")
            assert actual == expected_occupation, \
                f"职业识别失败: {text}, 期望 {expected_occupation}, 实际 {actual}"

    @pytest.mark.asyncio
    async def test_reading_level_coverage(self):
        """测试阅读水平关键词覆盖"""
        agent = RequirementAgent()

        level_tests = [
            ("Python入门教程", "入门"),
            ("算法进阶指南", "进阶"),
            ("高级编程技巧", "高级"),
            ("学术论文研究", "学术"),
        ]

        for text, expected_level in level_tests:
            result = await agent.analyze(text)
            actual = result.target_audience.get("reading_level")
            assert actual == expected_level, \
                f"阅读水平识别失败: {text}, 期望 {expected_level}, 实际 {actual}"

    @pytest.mark.asyncio
    async def test_age_group_coverage(self):
        """测试年龄段关键词覆盖"""
        agent = RequirementAgent()

        age_tests = [
            ("给小孩子看的书", "儿童"),
            ("青少年读物推荐", "青少年"),
            ("职场人士阅读", "成人"),
            ("适合老年人的书", "老年人"),
        ]

        for text, expected_age in age_tests:
            result = await agent.analyze(text)
            actual = result.target_audience.get("age_group")
            assert actual == expected_age, \
                f"年龄段识别失败: {text}, 期望 {expected_age}, 实际 {actual}"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
