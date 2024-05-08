CREATE TABLE IF NOT EXISTS `users` (
  `user_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `email` varchar(320) NOT NULL,
  `password` varchar(255) NOT NULL,
  `confirmed` BOOLEAN NOT NULL DEFAULT '0',
  `salt` varchar(32) NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `email` (`email`)
);


CREATE TABLE IF NOT EXISTS `verify_code` (
  `user_id` bigint unsigned NOT NULL,
  `code` varchar(6) NOT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `verify_code_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    token VARCHAR(28) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


ALTER TABLE password_reset_tokens
  CHANGE created_at created_at DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());


CREATE TABLE IF NOT EXISTS roles (
    role_id INT UNSIGNED PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);


CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT UNSIGNED NOT NULL,
    role_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `chat_gpt_keys` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `key` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS `gemini_keys` (
  `user_id` BIGINT UNSIGNED NOT NULL,
  `key` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS account_removal_tokens (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    token VARCHAR(28) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


ALTER TABLE account_removal_tokens
  CHANGE created_at created_at DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());


-- These are the current roles the database will support
INSERT IGNORE INTO roles (role_id, role_name) VALUES (1, 'admin'), (2, 'prompt_engineer');


CREATE TABLE IF NOT EXISTS running_tasks (
	process_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	user_id BIGINT UNSIGNED NOT NULL,
	uuid VARCHAR(36) UNIQUE NOT NULL,
	status ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING' NOT NULL,
	start_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	end_time DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
);


ALTER TABLE running_tasks CHANGE start_time start_time DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());
