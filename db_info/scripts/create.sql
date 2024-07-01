-- Tables
CREATE TABLE IF NOT EXISTS `users` (
  `user_id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `full_name` varchar(255) NOT NULL,
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


-- These are the current roles the database will support
INSERT IGNORE INTO roles (role_id, role_name) VALUES (1, 'admin'), (2, 'prompt_engineer'), (3, 'organizer');


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


CREATE TABLE IF NOT EXISTS challenge_drafts (
	id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(255),
  start_date DATETIME,
  end_date DATETIME,
  join_link VARCHAR(255) UNIQUE,
  public_visibility BOOL DEFAULT TRUE,
  description TEXT,
  rules TEXT,
  terms_service TEXT,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS challenges (
	id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  start_date DATETIME NOT NULL,
  end_date DATETIME NOT NULL,
  join_link VARCHAR(255) UNIQUE NOT NULL,
  public_visibility BOOL NOT NULL DEFAULT TRUE,
  description TEXT NOT NULL,
  rules TEXT NOT NULL,
  terms_service TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS challenge_organizer (
	user_id BIGINT UNSIGNED NOT NULL,
  challenge_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY(user_id, challenge_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS challenge_participants (
	user_id BIGINT UNSIGNED NOT NULL,
  challenge_id BIGINT UNSIGNED NOT NULL,
  date_joined DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(user_id, challenge_id),
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE ON UPDATE CASCADE
);


ALTER TABLE challenge_participants CHANGE date_joined date_joined DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());


CREATE TABLE IF NOT EXISTS challenge_announcements (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	challenge_id BIGINT UNSIGNED NOT NULL,
  announcement TEXT NOT NULL,
  announce_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE ON UPDATE CASCADE
);


ALTER TABLE challenge_announcements CHANGE announce_time announce_time DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());


CREATE TABLE IF NOT EXISTS results (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, 
  user_id BIGINT UNSIGNED NOT NULL,
  uuid VARCHAR(36) NOT NULL,
  scores JSON NOT NULL,
  finish_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  prompt TEXT NOT NULL,
  instructions TEXT NOT NULL,
  CONSTRAINT FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
);


ALTER TABLE results CHANGE finish_time finish_time DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());


CREATE TABLE IF NOT EXISTS result_in_challenge (
  result_id BIGINT UNSIGNED, 
  challenge_id BIGINT UNSIGNED,
  PRIMARY KEY(result_id, challenge_id),
  CONSTRAINT FOREIGN KEY (result_id) REFERENCES results(id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS running_task_challenge (
  task_id BIGINT UNSIGNED NOT NULL,
  challenge_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (task_id),
  FOREIGN KEY (task_id) REFERENCES running_tasks(process_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (challenge_id) REFERENCES challenges(id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS challenge_datasets (
  challenge_id BIGINT UNSIGNED PRIMARY KEY,
  file_name VARCHAR(70) NOT NULL,
  friendly_name VARCHAR(70) NOT NULL,
  num_rows INT UNSIGNED NOT NULL,
  subject VARCHAR(255),
  CONSTRAINT FOREIGN KEY(challenge_id) REFERENCES challenges(id) ON DELETE CASCADE ON UPDATE CASCADE
);


-- Views
CREATE OR REPLACE VIEW users_and_roles AS
SELECT 
    users.user_id,
    users.email,
    GROUP_CONCAT(roles.role_name) AS roles
FROM 
    users
LEFT JOIN 
    user_roles ON users.user_id = user_roles.user_id
LEFT JOIN 
    roles ON user_roles.role_id = roles.role_id
GROUP BY 
    users.user_id, users.email;


CREATE OR REPLACE VIEW challenge_scoreboard AS
SELECT 
    result_in_challenge.result_id,
    result_in_challenge.challenge_id,
    results.user_id,
    users.full_name,
    results.scores,
    results.prompt
FROM 
    result_in_challenge
LEFT JOIN 
    results
ON result_in_challenge.result_id = results.id
LEFT JOIN
	users
ON users.user_id = results.user_id;


CREATE OR REPLACE VIEW challenge_scoreboard_fscore AS
WITH user_scores AS (
    SELECT
        challenge_id,
        user_id,
        full_name,
        MAX(CAST(JSON_UNQUOTE(JSON_EXTRACT(scores, '$.fscore')) AS DECIMAL(10,2))) AS highest_fscore
    FROM 
        challenge_scoreboard
    GROUP BY 
        challenge_id, user_id, full_name
)
SELECT 
	  challenge_id,
    user_id,
    full_name,
    highest_fscore,
    RANK() OVER (PARTITION BY challenge_id ORDER BY highest_fscore DESC) AS ranking
FROM 
    user_scores
ORDER BY 
    ranking;


CREATE OR REPLACE VIEW registered_leaderboard_view AS
SELECT 
    challenges.id AS challenge_id, 
    challenges.name, 
    COALESCE(challenge_scoreboard_fscore.highest_fscore, 'N/A') AS highest_fscore, 
    COALESCE(challenge_scoreboard_fscore.ranking, 'N/A') AS ranking, 
    challenges.start_date, 
    challenges.end_date,
    challenge_participants.user_id
FROM 
    challenges
LEFT JOIN
	  challenge_participants
ON
	  challenges.id = challenge_participants.challenge_id
LEFT JOIN 
    challenge_scoreboard_fscore
ON 
    challenges.id = challenge_scoreboard_fscore.challenge_id
    AND challenge_scoreboard_fscore.user_id = challenge_participants.user_id
ORDER BY 
    challenge_scoreboard_fscore.highest_fscore DESC;
