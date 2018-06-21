CREATE TABLE IF NOT EXISTS attachment(
    attachment_id           INT(10) NOT NULL AUTO_INCREMENT COMMENT 'unique id for each attachment',
    mail_id                 INT(10) NOT NULL COMMENT 'id of email',
    attachment_hash         VARCHAR(40) NOT NULL COMMENT 'unique md5 hash for each unique attachment',
    path_to_attachment_file VARCHAR(255) NOT NULL COMMENT 'path to original binary file on NFS',
    attachment_name                    VARCHAR(255) NOT NULL COMMENT 'attachment\'s name',
    attachment_size         INT(10) NOT NULL COMMENT 'attachment\'s byte size',
    attachment_type                    VARCHAR(255) NOT NULL COMMENT 'attachment\'s content type',
    PRIMARY KEY (attachment_id),
    INDEX mail_id (mail_id),
    FOREIGN KEY (mail_id)
        REFERENCES metadata(mail_id)
            ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE = utf8mb4_general_ci;

