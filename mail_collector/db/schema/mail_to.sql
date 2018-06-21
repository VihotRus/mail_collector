CREATE TABLE IF NOT EXISTS mail_to(
    recipient_id INT(10) NOT NULL AUTO_INCREMENT COMMENT 'unique id for each email recipient',
    mail_id      INT(10) NOT NULL COMMENT 'email id',
    mail_recipient    VARCHAR(255) NOT NULL COMMENT 'email\'s recipient',
    PRIMARY KEY (recipient_id),
    INDEX email_id(mail_id),
    FOREIGN KEY (mail_id)
        REFERENCES metadata(mail_id)
            ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_general_ci;

