"""
书目筛选词配置模块

定义图书筛选分类和关键词，用于排除特定类型的图书
如教育教辅类、儿童读物类等
"""

from typing import Dict, List


class FilterCategory:
    """筛选分类类"""

    def __init__(self, code: str, name: str, description: str, keywords: List[str]):
        self.code = code  # 分类代码
        self.name = name  # 分类名称
        self.description = description  # 分类描述
        self.keywords = keywords  # 关键词列表


# 筛选词配置
FILTER_KEYWORDS_CONFIG: List[Dict] = [
    {
        "code": "education",
        "name": "教育教辅",
        "description": "排除教育类、教材类、教辅类图书",
        "keywords": [
            # 学校相关
            "学生", "学校", "校园", "小学", "中学", "初中", "高中", "大学", "高校", "高职",
            # 教师相关
            "教师", "老师", "班主任",
            # 教材教辅
            "教材", "练习册", "作业本", "试卷", "题", "考试", "卷", "四特",
            # 学科
            "语文", "数学", "物理", "化学", "英语", "生物", "历史", "地理", "政治",
            # 教育相关
            "教学", "课堂", "年级", "新课标", "统编", "考研", "中考", "高考",
            # 教育机构
            "博识教育", "优等生",
        ]
    },
    {
        "code": "children",
        "name": "儿童读物",
        "description": "排除儿童、少儿、幼儿类读物",
        "keywords": [
            # 年龄相关
            "幼儿", "儿童", "少儿", "亲子", "男孩", "女孩", "宝宝", "宝贝", "孩子",
            "小孩", "岁", "少年", "青少年",
            # 阅读相关
            "注音", "拼音", "绘本", "彩绘", "美绘", "漫画", "动画", "插图",
            # 色彩相关
            "四色", "彩图", "全彩", "彩色",
            # 儿童文学作者
            "曹文轩", "沈石溪", "阳光姐姐", "小豆子",
            # 儿童相关
            "班级", "虹猫", "赛尔号", "洛克王国", "麦咭", "小笨熊", "常春藤",
            "植物大战僵尸",
        ]
    },
    {
        "code": "directory",
        "name": "成人目录",
        "description": "排除成人用品目录类图书",
        "keywords": ["成人目录"]
    }
]


def get_filter_categories() -> Dict[str, FilterCategory]:
    """获取所有筛选分类"""
    categories = {}
    for config in FILTER_KEYWORDS_CONFIG:
        categories[config["code"]] = FilterCategory(
            code=config["code"],
            name=config["name"],
            description=config["description"],
            keywords=config["keywords"]
        )
    return categories


def get_all_keywords() -> List[str]:
    """获取所有筛选关键词"""
    all_keywords = []
    for config in FILTER_KEYWORDS_CONFIG:
        all_keywords.extend(config["keywords"])
    return list(set(all_keywords))  # 去重


def get_keywords_by_category(category_code: str) -> List[str]:
    """获取指定分类的关键词"""
    for config in FILTER_KEYWORDS_CONFIG:
        if config["code"] == category_code:
            return config["keywords"]
    return []


# 导出筛选分类实例
FILTER_CATEGORIES = get_filter_categories()
ALL_FILTER_KEYWORDS = get_all_keywords()


if __name__ == "__main__":
    # 测试代码
    print("筛选分类配置:")
    for code, category in FILTER_CATEGORIES.items():
        print(f"\n{category.name} ({code}):")
        print(f"  描述: {category.description}")
        print(f"  关键词数量: {len(category.keywords)}")
        print(f"  关键词: {', '.join(category.keywords[:10])}...")

    print(f"\n总关键词数量: {len(ALL_FILTER_KEYWORDS)}")
