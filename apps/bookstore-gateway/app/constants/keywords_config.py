"""
关键词配置文件
用于需求分析和用户意图识别
"""

# 目标受众 - 职业维度
TARGET_AUDIENCE_OCCUPATION = {
    "大学生": ["大学", "学生", "本科", "研究生", "博士生", "考研", "在校生", "校园", "学期"],
    "程序员": ["程序员", "开发", "编程", "代码", "软件", "工程师", "developer", "coder", "码农"],
    "教师": ["教师", "老师", "教授", "讲师", "教员", "教育工作者"],
    "产品经理": ["产品经理", "pm", "产品", "需求", "用户研究", "交互"],
    "设计师": ["设计师", "设计", "ui", "ux", "视觉", "平面", "交互设计"],
    "数据分析师": ["数据", "分析", "分析师", "analytics", "数据科学", "统计"],
    "运营": ["运营", "新媒体", "内容运营", "用户运营", "社群", "裂变"],
    "销售": ["销售", "业务员", "客户经理", "商务", "市场拓展"],
    "金融从业者": ["金融", "证券", "基金", "银行", "投资", "理财", "股票"],
    "医疗从业者": ["医生", "护士", "医疗", "临床", "医学"],
    "法律从业者": ["律师", "法务", "法律", "司法"],
    "创业者": ["创业", "企业家", "老板", "创始人", "ceo"],
    "自由职业": ["自由职业", "soho", "独立", "个体"],
    "管理者": ["管理者", "管理", "领导", "主管", "总监", "cxo"],
    "研究员": ["研究员", "科研", "学术", "研究", "学者"],
}

# 目标受众 - 年龄维度
TARGET_AUDIENCE_AGE = {
    "儿童": ["儿童", "小朋友", "小孩", "幼儿", "学前", "小学", "少儿"],
    "青少年": ["青少年", "初中", "高中", "中学生", "青春期"],
    "成人": ["成人", "工作", "职场", "成人", "青年"],
    "老年人": ["老年", "老人", "退休", "养老", "长者", "银发"],
}

# 目标受众 - 阅读水平
READING_LEVEL = {
    "入门": ["入门", "基础", "新手", "零基础", "初学", "小白", "快速上手", "从零开始"],
    "进阶": ["进阶", "提升", "深入", "提高", "中级", "进阶学习"],
    "高级": ["高级", "专家", "精通", "深度", "前沿", "专业", "高级教程"],
    "学术": ["学术", "研究", "论文", "理论", "教材", "专著"],
}

# 书籍分类 - 主题维度
BOOK_CATEGORIES = {
    "编程": ["编程", "代码", "开发", "程序", "软件", "algorithm", "coding", "programming"],
    "算法": ["算法", "数据结构", "算法设计", "算法导论", "复杂度"],
    "人工智能": ["人工智能", "ai", "机器学习", "深度学习", "ml", "neural", "tensorflow", "pytorch"],
    "前端": ["前端", "前端开发", "web", "html", "css", "javascript", "vue", "react", "angular"],
    "后端": ["后端", "服务端", "server", "api", "微服务", "分布式"],
    "数据库": ["数据库", "database", "mysql", "postgresql", "mongodb", "redis"],
    "运维": ["运维", "devops", "容器", "docker", "k8s", "kubernetes", "部署", "ci/cd"],
    "测试": ["测试", "test", "自动化测试", "质量", "qa"],
    "产品": ["产品", "产品设计", "用户体验", "ue", "交互设计", "prd"],
    "设计": ["设计", "ui", "ux", "视觉", "平面", "配色", "排版", "设计模式"],
    "数据科学": ["数据", "大数据", "分析", "analytics", "可视化", "数据挖掘"],
    "商业": ["商业", "business", "商业模式", "创业", "管理", "营销"],
    "经济": ["经济", "金融", "投资", "理财", "股票", "基金", "证券"],
    "历史": ["历史", "朝代", "古代", "近代", "世界史", "中国史"],
    "文学": ["文学", "小说", "散文", "诗歌", "名著", "经典", "阅读"],
    "科普": ["科普", "科学", "自然", "物理", "化学", "生物"],
    "传记": ["传记", "人物", "自传", "回忆录", "名人"],
    "哲学": ["哲学", "思想", "逻辑", "伦理", "思考"],
    "心理": ["心理", "心理学", "认知", "行为", "情绪", "心智"],
    "教育": ["教育", "学习", "教学", "培训", "考试"],
    "职场": ["职场", "工作", "沟通", "团队", "管理", "领导力"],
    "生活": ["生活", "健康", "养生", "美食", "旅行"],
}

# 约束条件关键词
CONSTRAINT_KEYWORDS = {
    "budget": ["预算", "元", "价格", "费用", "成本", "便宜", "实惠"],
    "exclude_textbooks": ["非教材", "不要教材", "排除教材", "不含教材"],
    "latest": ["最新", "新版", "2024", "2025", "新出版"],
    "classic": ["经典", "名著", "畅销", "必读"],
    "language_cn": ["中文", "国内", "中文版"],
    "language_en": ["英文", "原版", "英文版", "外文"],
}

# 置信度阈值配置
CONFIDENCE_THRESHOLD = {
    "HIGH": 0.8,  # 高置信度，直接使用
    "MEDIUM": 0.5,  # 中等置信度，可以补充信息
    "LOW": 0.3  # 低置信度，必须澄清
}

# 澄清问题模板
CLARIFICATION_QUESTIONS = {
    "occupation": "请问这本书是推荐给哪类人群的？例如：程序员、教师、大学生、产品经理等",
    "age": "请问读者的年龄段是？例如：儿童、青少年、成人、老年人",
    "level": "请问读者的阅读水平是？例如：入门、进阶、高级",
    "category": "请问您希望推荐哪个主题的书籍？例如：编程、设计、商业、历史等",
    "budget": "请问您的预算范围是多少？",
    "general": "能否更详细地描述您的阅读需求？例如：目标读者、主题偏好、预算范围等",
}


def get_all_keywords():
    """
    获取所有关键词的扁平化列表，用于快速匹配

    Returns:
        set: 所有关键词的集合
    """
    all_keywords = set()

    for category_dict in [TARGET_AUDIENCE_OCCUPATION, TARGET_AUDIENCE_AGE,
                          READING_LEVEL, BOOK_CATEGORIES, CONSTRAINT_KEYWORDS]:
        for keywords in category_dict.values():
            all_keywords.update(keywords)

    return all_keywords


def get_category_by_keyword(keyword: str) -> dict:
    """
    根据关键词查找对应的分类

    Args:
        keyword: 关键词

    Returns:
        dict: {类型: 分类名} 的字典
    """
    result = {}

    # 检查职业
    for occupation, keywords in TARGET_AUDIENCE_OCCUPATION.items():
        if keyword.lower() in [k.lower() for k in keywords]:
            result["occupation"] = occupation
            break

    # 检查年龄
    for age, keywords in TARGET_AUDIENCE_AGE.items():
        if keyword.lower() in [k.lower() for k in keywords]:
            result["age"] = age
            break

    # 检查阅读水平
    for level, keywords in READING_LEVEL.items():
        if keyword.lower() in [k.lower() for k in keywords]:
            result["level"] = level
            break

    # 检查书籍分类
    for category, keywords in BOOK_CATEGORIES.items():
        if keyword.lower() in [k.lower() for k in keywords]:
            result["category"] = category
            break

    return result


# 导出配置
__all__ = [
    "TARGET_AUDIENCE_OCCUPATION",
    "TARGET_AUDIENCE_AGE",
    "READING_LEVEL",
    "BOOK_CATEGORIES",
    "CONSTRAINT_KEYWORDS",
    "CONFIDENCE_THRESHOLD",
    "CLARIFICATION_QUESTIONS",
    "get_all_keywords",
    "get_category_by_keyword",
]
