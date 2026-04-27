-- BookStore 数据库脚本
CREATE DATABASE IF NOT EXISTS bookstore CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bookstore;

-- 1. 用户表
CREATE TABLE IF NOT EXISTS t_user (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    status ENUM('active','inactive') DEFAULT 'active',
    last_login_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 书籍信息表
CREATE TABLE IF NOT EXISTS t_book_info (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(64) NOT NULL,
    title VARCHAR(512) NOT NULL,
    title_clean VARCHAR(512) NOT NULL,
    author VARCHAR(256),
    publisher VARCHAR(256),
    series VARCHAR(256),
    price DECIMAL(10,2),
    stock INT UNSIGNED DEFAULT 0,
    discount DECIMAL(5,4) DEFAULT 0,
    embedding LONGTEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    semantic_description TEXT,
    categories JSON,
    cognitive_level VARCHAR(20) DEFAULT '通用',
    target_audience JSON,
    difficulty_level INT DEFAULT 5,
    prerequisites JSON,
    tags JSON,
    publication_year INT,
    language VARCHAR(20) DEFAULT '中文',
    page_count INT,
    isbn VARCHAR(20),
    vector_id VARCHAR(100),
    UNIQUE KEY uk_barcode (barcode),
    INDEX idx_title_author (title_clean(200), author),
    INDEX idx_author_series (author, series),
    INDEX idx_discount_stock (discount, stock)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 补货计划表
CREATE TABLE IF NOT EXISTS t_replenishment_plan (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    book_id BIGINT UNSIGNED NOT NULL,
    suggest_qty INT UNSIGNED NOT NULL,
    plan_status ENUM('pending','urgent','approved','rejected') DEFAULT 'pending',
    reason VARCHAR(512),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_plan_book (book_id),
    INDEX idx_plan_status (plan_status, create_time),
    CONSTRAINT fk_plan_book FOREIGN KEY (book_id) REFERENCES t_book_info(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 用户行为表
CREATE TABLE IF NOT EXISTS t_user_behavior (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    book_id BIGINT UNSIGNED NOT NULL,
    action_type ENUM('view','purchase','favorite','cart','review') NOT NULL,
    rating DECIMAL(2,1),
    duration INT,
    context JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_action (user_id, action_type, created_at),
    INDEX idx_book_action (book_id, action_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 用户画像表
CREATE TABLE IF NOT EXISTS t_user_profile (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL UNIQUE,
    age_group VARCHAR(20),
    education_level VARCHAR(50),
    occupation VARCHAR(100),
    reading_preferences JSON,
    cognitive_preference VARCHAR(20) DEFAULT '中等',
    favorite_categories JSON,
    behavior_summary JSON,
    last_analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES t_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 书单模板表
CREATE TABLE IF NOT EXISTS t_book_list_template (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL,
    target_audience VARCHAR(100) NOT NULL,
    description TEXT,
    category_requirements JSON,
    difficulty_level VARCHAR(20) DEFAULT '中等',
    book_count INT DEFAULT 20,
    is_active BOOLEAN DEFAULT TRUE,
    created_by BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_template_audience (target_audience),
    INDEX idx_template_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 定制书单记录表
CREATE TABLE IF NOT EXISTS t_custom_book_list (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    request_text TEXT NOT NULL,
    parsed_requirements JSON,
    book_list JSON NOT NULL,
    status ENUM('pending','processing','completed','failed') DEFAULT 'pending',
    error_message TEXT,
    processing_time INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    INDEX idx_user_status (user_id, status),
    INDEX idx_created_time (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. RAG查询缓存表
CREATE TABLE IF NOT EXISTS t_rag_cache (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL UNIQUE,
    query_text TEXT NOT NULL,
    result JSON NOT NULL,
    hit_count INT DEFAULT 1,
    last_hit_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX idx_hash (query_hash),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. 智能查重记录表
CREATE TABLE IF NOT EXISTS t_duplicate_detection (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    query_book_id BIGINT UNSIGNED NOT NULL,
    candidate_book_id BIGINT UNSIGNED NOT NULL,
    similarity_score DECIMAL(5,4) NOT NULL,
    detection_method ENUM('semantic','metadata','hybrid') NOT NULL,
    is_confirmed BOOLEAN DEFAULT NULL,
    confirmed_by BIGINT UNSIGNED,
    confirmed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_query_book (query_book_id),
    INDEX idx_candidate_book (candidate_book_id),
    INDEX idx_score_desc (similarity_score DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. 系统配置表
CREATE TABLE IF NOT EXISTS t_system_config (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value JSON NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    updated_by BIGINT UNSIGNED,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 初始化配置数据
INSERT INTO t_system_config (config_key, config_value, description) VALUES
('rag_embedding_model', '{"model_name": "BAAI/bge-large-zh", "dimension": 1024, "max_length": 512}', '嵌入模型配置'),
('rag_vector_db', '{"host": "localhost", "port": 6333, "collection": "bookstore"}', '向量数据库配置'),
('rag_llm_config', '{"provider": "openai", "model": "gpt-3.5-turbo", "temperature": 0.7, "max_tokens": 2000}', 'LLM配置'),
('rag_search_params', '{"top_k": 20, "score_threshold": 0.7, "rerank_top_k": 10}', '检索参数'),
('rag_cache_config', '{"ttl_seconds": 3600, "max_size": 1000}', '缓存配置')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- 初始化书单模板
INSERT INTO t_book_list_template (template_name, target_audience, description, category_requirements) VALUES
('大学生基础书单', '大学生', '适合大学生阅读的基础书籍', '{"文学": 0.25, "科技": 0.25, "历史": 0.2, "艺术": 0.15, "哲学": 0.15}'),
('职场新人书单', '职场新人', '帮助职场新人成长的实用书籍', '{"职业技能": 0.4, "沟通": 0.2, "思维": 0.2, "管理": 0.2}'),
('技术开发书单', '开发者', '程序员和技术开发者书单', '{"编程": 0.4, "架构": 0.2, "算法": 0.2, "工具": 0.2}')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
