CREATE TABLE IF NOT EXISTS metadata(
    mail_id           INT(10) NOT NULL AUTO_INCREMENT COMMENT 'unique id for each email',
    mail_from         VARCHAR(255) NOT NULL COMMENT 'email sender',
    mail_subject      VARCHAR(255) COMMENT 'email\'s subject',
    path_to_text_body VARCHAR(255) COMMENT 'email\'s path to text body',
    path_to_html_body VARCHAR(255) COMMENT 'email\'s path to html body',
    path_to_original  VARCHAR(255) COMMENT 'email\'s path to original',
    mail_date         INT(11) NOT NULL COMMENT 'the date and time email was composed in TIMESTAMP format',
    PRIMARY KEY (mail_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_general_ci;

