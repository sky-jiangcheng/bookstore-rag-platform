-- 智能书单推荐会话表迁移脚本
-- 执行日期: 2026-02-01
-- 目的: 支持交互式书单推荐功能

-- 1. 创建书单会话表
CREATE TABLE IF NOT EXISTS `t_book_list_session` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `request_id` VARCHAR(64) NOT NULL UNIQUE COMMENT '请求ID（UUID）',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    
    -- 用户输入
    `original_input` TEXT NOT NULL COMMENT '用户原始输入',
    `refined_inputs` JSON DEFAULT NULL COMMENT '历次细化输入列表',
    
    -- 后端理解（解析结果）
    `parsed_requirements` JSON NOT NULL COMMENT '解析后的需求（最新版本）',
    `parsing_history` JSON DEFAULT NULL COMMENT '解析历史记录',
    
    -- 会话状态
    `status` VARCHAR(20) NOT NULL DEFAULT 'parsing' COMMENT '状态：parsing/waiting_confirmation/refining/confirmed/generating/completed/failed',
    
    -- 用户反馈
    `user_feedbacks` JSON DEFAULT NULL COMMENT '用户反馈历史',
    `confirmation_count` INT DEFAULT 0 COMMENT '确认次数',
    `refinement_count` INT DEFAULT 0 COMMENT '细化次数',
    
    -- 生成结果
    `book_list_id` BIGINT DEFAULT NULL COMMENT '生成的书单ID',
    `generation_params` JSON DEFAULT NULL COMMENT '最终生成参数',
    
    -- 性能指标
    `parsing_time_ms` INT DEFAULT NULL COMMENT '解析耗时（毫秒）',
    `generation_time_ms` INT DEFAULT NULL COMMENT '生成耗时（毫秒）',
    `total_time_ms` INT DEFAULT NULL COMMENT '总耗时（毫秒）',
    
    -- 错误信息
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    
    -- 时间戳
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `confirmed_at` TIMESTAMP DEFAULT NULL COMMENT '确认时间',
    `completed_at` TIMESTAMP DEFAULT NULL COMMENT '完成时间',
    
    -- 索引
    KEY `idx_request_id` (`request_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_status` (`status`),
    KEY `idx_created_at` (`created_at`),
    
    -- 外键
    CONSTRAINT `fk_session_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_session_book_list` FOREIGN KEY (`book_list_id`) REFERENCES `t_custom_book_list` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='书单推荐会话表';

-- 2. 创建会话反馈表
CREATE TABLE IF NOT EXISTS `t_session_feedback` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `session_id` BIGINT NOT NULL COMMENT '会话ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    
    -- 反馈内容
    `feedback_type` VARCHAR(20) NOT NULL COMMENT '反馈类型：confirmation/refinement/rejection/satisfaction',
    `feedback_content` TEXT DEFAULT NULL COMMENT '反馈内容',
    `feedback_data` JSON DEFAULT NULL COMMENT '结构化反馈数据',
    
    -- 反馈前后对比
    `before_requirements` JSON DEFAULT NULL COMMENT '反馈前的需求',
    `after_requirements` JSON DEFAULT NULL COMMENT '反馈后的需求',
    
    -- 时间戳
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 索引
    KEY `idx_session_id` (`session_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_feedback_type` (`feedback_type`),
    KEY `idx_created_at` (`created_at`),
    
    -- 外键
    CONSTRAINT `fk_feedback_session` FOREIGN KEY (`session_id`) REFERENCES `t_book_list_session` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_feedback_user` FOREIGN KEY (`user_id`) REFERENCES `t_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话反馈表';

-- 3. 为现有表添加索引优化（如果不存在）
ALTER TABLE `t_custom_book_list` 
ADD INDEX IF NOT EXISTS `idx_user_created` (`user_id`, `created_at`);

-- 4. 验证表创建
SELECT 
    'Tables created successfully' AS status,
    (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 't_book_list_session') AS session_table_exists,
    (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 't_session_feedback') AS feedback_table_exists;

-- 5. 说明
-- 使用方法：
-- mysql -u root -p bookstore < migration_book_list_session.sql
-- 
-- 回滚方法（如需）：
-- DROP TABLE IF EXISTS `t_session_feedback`;
-- DROP TABLE IF EXISTS `t_book_list_session`;
