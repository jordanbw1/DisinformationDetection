-- Create placeholder tables for copying data
CREATE TABLE IF NOT EXISTS temp_competition_data (
    competition_id BIGINT UNSIGNED PRIMARY KEY,
    scoreboard_visibility BOOL NOT NULL DEFAULT TRUE,
    public BOOL NOT NULL DEFAULT FALSE,
    description TEXT,
    rules TEXT,
    terms_service TEXT
);

CREATE TABLE IF NOT EXISTS temp_results_data (
    result_id BIGINT UNSIGNED PRIMARY KEY, 
    prompt TEXT,
    instructions TEXT
);


-- Copy data into temporary table
-- Copy data from competition_settings
INSERT INTO temp_competition_data (competition_id, scoreboard_visibility, public)
SELECT competition_id, scoreboard_visibility, public
FROM competition_settings;

-- Copy data from competition_details
UPDATE temp_competition_data t
JOIN competition_details d ON t.competition_id = d.competition_id
SET t.description = d.description,
    t.rules = d.rules,
    t.terms_service = d.terms_service;

-- Copy data for results table
INSERT INTO temp_results_data (result_id, prompt, instructions)
SELECT result_id, COALESCE(prompt, 'N/A'), COALESCE(instructions, 'N/A')
FROM results_additional_info;


-- Tables
-- Handle users
ALTER TABLE `users`
MODIFY COLUMN `full_name` VARCHAR(255) NOT NULL;


-- Create challenge drafts
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


-- Handle competition
-- Rename competitions
ALTER TABLE competitions RENAME TO challenges;
-- Handle null values
UPDATE challenges SET 
    start_date = '2050-01-01' WHERE start_date IS NULL;
UPDATE challenges SET
    end_date = '2050-01-01' WHERE end_date IS NULL;
-- Add new columns
ALTER TABLE challenges
ADD COLUMN public_visibility BOOL NOT NULL DEFAULT TRUE,
ADD COLUMN description TEXT NOT NULL,
ADD COLUMN rules TEXT NOT NULL,
ADD COLUMN terms_service TEXT NOT NULL;
-- Set correct constraints for dates
ALTER TABLE challenges 
MODIFY COLUMN start_date DATETIME NOT NULL,
MODIFY COLUMN end_date DATETIME NOT NULL;


-- Handle competition_organizer
-- Rename the table from competition_organizer to challenge_organizer
ALTER TABLE competition_organizer RENAME TO challenge_organizer;
-- Modify foreign key from competition_id to challenge_id
ALTER TABLE challenge_organizer
RENAME COLUMN competition_id to challenge_id;
-- Add primary key on (user_id, challenge_id)
ALTER TABLE challenge_organizer
ADD PRIMARY KEY (user_id, challenge_id);


-- Handle competition_participants
-- Rename the table
ALTER TABLE competition_participants RENAME TO challenge_participants;
-- Modify column names and foreign key references
ALTER TABLE challenge_participants
RENAME COLUMN competition_id to challenge_id;
-- Add primary key
ALTER TABLE challenge_participants
ADD PRIMARY KEY (user_id, challenge_id);
-- Fix time
ALTER TABLE challenge_participants CHANGE date_joined date_joined DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());


-- Handle competition_announcements
-- Rename the table
ALTER TABLE competition_announcements RENAME TO challenge_announcements;
-- Modify column name and foreign key reference
ALTER TABLE challenge_announcements
RENAME COLUMN competition_id to challenge_id;
-- Fix time
ALTER TABLE challenge_announcements CHANGE announce_time announce_time DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());


-- Handle Results
ALTER TABLE results
ADD COLUMN prompt TEXT NOT NULL,
ADD COLUMN instructions TEXT NOT NULL;
-- Fix time
ALTER TABLE results CHANGE finish_time finish_time DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP());


-- Handle result_in_competition
-- Rename the table
ALTER TABLE result_in_competition RENAME TO result_in_challenge;
-- Modify column names and foreign key references
ALTER TABLE result_in_challenge
RENAME COLUMN competition_id to challenge_id;


-- Handle running_task_competition
-- Rename the table from running_task_competition to running_task_challenge
ALTER TABLE running_task_competition RENAME TO running_task_challenge;
-- Modify column name and foreign key reference to point to challenges table
ALTER TABLE running_task_challenge
RENAME COLUMN competition_id to challenge_id;


-- Handle competition_datasets
-- Rename the table from competition_datasets to challenge_datasets
ALTER TABLE competition_datasets RENAME TO challenge_datasets;
-- Modify column name and foreign key reference to point to challenges table
ALTER TABLE challenge_datasets
RENAME COLUMN competition_id to challenge_id;



-- Drop old views
DROP VIEW IF EXISTS competition_scoreboard;
DROP VIEW IF EXISTS competition_scoreboard_fscore;



-- Drop tables
DROP TABLE IF EXISTS competition_settings;
DROP TABLE IF EXISTS competition_details;
DROP TABLE IF EXISTS competition_configured;
DROP TABLE IF EXISTS results_additional_info;



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


-- Copy data from temporary tables into the correct tables
-- Handle challenges
UPDATE challenges c
JOIN temp_competition_data tc ON c.id = tc.competition_id
SET 
    c.public_visibility = tc.public,
    c.description = tc.description,
    c.rules = tc.rules,
    c.terms_service = tc.terms_service;



-- Handle results
UPDATE results r
JOIN temp_results_data tr ON r.id = tr.result_id
SET
    r.prompt = tr.prompt,
    r.instructions = tr.instructions;



-- Drop temporary tables
DROP TABLE IF EXISTS temp_competition_data;
DROP TABLE IF EXISTS temp_results_data;