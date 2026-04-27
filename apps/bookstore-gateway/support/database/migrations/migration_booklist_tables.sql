-- 书单模板和反馈表结构迁移脚本
-- 执行此脚本以添加书单推荐功能所需的数据库表

USE bookstore;

-- 1. 书单模板表
CREATE TABLE IF NOT EXISTS book_list_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    user_id INT NOT NULL COMMENT '创建用户ID',
    book_count INT DEFAULT 10 COMMENT '推荐书籍数量',
    budget INT DEFAULT 500 COMMENT '预算范围',
    difficulty VARCHAR(50) COMMENT '难度等级',
    goals JSON COMMENT '阅读目标列表',
    categories JSON COMMENT '分类需求',
    keywords JSON COMMENT '关键词列表',
    constraints JSON COMMENT '约束条件',
    parsed_requirements JSON COMMENT '预设的解析结果',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    like_count INT DEFAULT 0 COMMENT '点赞数',
    share_count INT DEFAULT 0 COMMENT '分享数',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统模板',
    tags JSON COMMENT '标签列表',
    thumbnail VARCHAR(500) COMMENT '缩略图URL',
    cover_image VARCHAR(500) COMMENT '封面图URL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_is_public_active (is_public, is_active),
    INDEX idx_is_system (is_system)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 书单满意度反馈表
CREATE TABLE IF NOT EXISTS book_list_feedbacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booklist_id VARCHAR(100) NOT NULL COMMENT '书单ID',
    booklist_name VARCHAR(200) COMMENT '书单名称',
    user_id INT NOT NULL COMMENT '用户ID',
    overall_score INT COMMENT '总体评分(1-5)',
    accuracy_score INT COMMENT '推荐准确性(1-5)',
    price_score INT COMMENT '价格合理性(1-5)',
    diversity_score INT COMMENT '书籍多样性(1-5)',
    suggestions TEXT COMMENT '改进建议',
    selected_books JSON COMMENT '选中的书籍ID列表',
    book_count INT COMMENT '书籍数量',
    total_price INT COMMENT '总价格',
    average_score INT COMMENT '平均匹配度',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_booklist_id (booklist_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 插入系统预设模板
INSERT INTO book_list_templates (
    name, description, user_id, book_count, budget, difficulty,
    goals, keywords, tags, is_public, is_system, usage_count
) VALUES
(
    'Python入门学习',
    '适合初学者的Python编程书籍，包含基础语法、实战项目、进阶话题等',
    1,
    10,
    500,
    'beginner',
    JSON_ARRAY('学习编程语言'),
    JSON_ARRAY('Python', '编程', '入门', '基础', '实战'),
    JSON_ARRAY('编程', 'Python', '入门'),
    TRUE,
    TRUE,
    0
),
(
    '数据分析入门',
    '数据分析基础书籍，涵盖统计学、Python数据分析工具、可视化等内容',
    1,
    8,
    400,
    'beginner',
    JSON_ARRAY('数据分析'),
    JSON_ARRAY('数据分析', '统计', 'Python', 'Pandas', '可视化'),
    JSON_ARRAY('数据分析', '统计', '可视化'),
    TRUE,
    TRUE,
    0
),
(
    '机器学习进阶',
    '适合有一定基础的读者，涵盖算法原理、框架使用、项目实战等',
    1,
    12,
    800,
    'advanced',
    JSON_ARRAY('机器学习'),
    JSON_ARRAY('机器学习', '深度学习', '算法', 'TensorFlow', 'PyTorch'),
    JSON_ARRAY('机器学习', 'AI', '深度学习'),
    TRUE,
    TRUE,
    0
),
(
    'Web开发全栈',
    'Web前端和后端开发书籍，包含HTML/CSS/JavaScript、框架、数据库等',
    1,
    15,
    600,
    'intermediate',
    JSON_ARRAY('Web开发'),
    JSON_ARRAY('Web', '前端', '后端', 'JavaScript', 'Vue', 'React'),
    JSON_ARRAY('Web开发', '前端', '后端'),
    TRUE,
    TRUE,
    0
),
(
    '大学生通用阅读',
    '适合大学生的综合阅读书单，涵盖文学、历史、哲学、科技等多个领域',
    1,
    20,
    800,
    'intermediate',
    JSON_ARRAY('综合阅读'),
    JSON_ARRAY('文学', '历史', '哲学', '科技', '社会科学'),
    JSON_ARRAY('大学生', '综合', '阅读'),
    TRUE,
    TRUE,
    0
);

-- 提交事务
COMMIT;
