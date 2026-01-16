-- AI Agent Framework 数据库初始化脚本
-- 适用于 MySQL 8.0+

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_agent DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_agent;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    hashed_password VARCHAR(255) NOT NULL COMMENT '密码哈希',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否激活',
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否超级用户',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 插入默认管理员账号
-- 密码: 111111 (bcrypt哈希)
INSERT INTO users (username, email, hashed_password, is_active, is_superuser)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$yzBahATtzjJT9Q3yVI1pAOa682lbVAaOQKuhAEyfAboNuzVSwqA2C',
    TRUE,
    TRUE
) ON DUPLICATE KEY UPDATE hashed_password='$2b$12$yzBahATtzjJT9Q3yVI1pAOa682lbVAaOQKuhAEyfAboNuzVSwqA2C';

-- 更新已有admin用户的密码（如果需要）
-- UPDATE users SET hashed_password='$2b$12$yzBahATtzjJT9Q3yVI1pAOa682lbVAaOQKuhAEyfAboNuzVSwqA2C' WHERE username='admin';

-- 查看表结构
-- DESCRIBE users;

-- 查看已创建的用户
-- SELECT id, username, email, is_active, is_superuser, created_at FROM users;
