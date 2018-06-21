#!/usr/bin/python

# db module which is working with database quieries

import MySQLdb
from src.config_init import config, logger

#section from config to connect database
DB_SECTION = 'mysqld'

def db_connection(func):
    # Database connection decorator
    #   which returns function result and
    #   commiting changes if no errors occured
    #   otherwise returns error str
    def wrapper(*args, **kwargs):
        logger.info("connecting to db")
        cnx = MySQLdb.connect(
                    host=config.get(DB_SECTION, 'host'),
                    user=config.get(DB_SECTION, 'user'),
                    passwd=config.get(DB_SECTION, 'passwd'),
                    db=config.get(DB_SECTION, 'db'),
                    charset=config.get(DB_SECTION, 'charset')
                    )
        logger.debug("Connected %s" % (cnx, ))
        try:
            logger.debug("Calling func %s " % (func.__name__, ))
            result = func(cnx, *args, **kwargs)
            logger.info("Commiting changes")
            cnx.commit()
        except Exception as error:
            logger.info("Error occured")
            logger.error(error)
            logger.info("Rollbacking changes")
            cnx.rollback()
            result = error.args[-1]
        finally:
            logger.debug("Closing connection %s" % (cnx, ))
            cnx.close()
        return result
    return wrapper

@db_connection
def data_insertion_mysql(cnx, payload):
    # Function which is inserting data to mysql from mail payload
    # Args:
    #   payload(dict) - email payload with parsed metadata
    cursor = cnx.cursor()
    # define payload keys which belongs to metadata table
    metadata_keys = ['FROM', 'Subject', 'Original', 'Text body', 'Html body', 'Date']
    # taking params for metadata table
    metadata_params = [payload.get(key) for key in metadata_keys]
    # sql expression to insert data into metadata table
    metadata_insertion = ("INSERT INTO metadata"
               "(mail_from, mail_subject, path_to_original, "
               "path_to_text_body, path_to_html_body, mail_date) "
               "VALUES (%s, %s, %s, %s, %s, %s)")
    logger.info("executing inserting to metadata table")
    cursor.execute(metadata_insertion, metadata_params)
    # getting mail_id from the last insertinon
    mail_id = cnx.insert_id()
    logger.debug("insertion id %s" % (mail_id, ))
    # getting recipients list from mail payload
    recipients = payload.get('TO')
    # sql expression to insert data into mail_to table
    mail_to_insertion = ("INSERT INTO mail_to"
               "(mail_id, mail_recipient) "
               "VALUES (%s, %s)")
    # insert every recipient from list
    for recipient in recipients:
        logger.info("executing inserting to mail_to table")
        cursor.execute(mail_to_insertion, (mail_id, recipient))
    # getting attachments list from mail payload
    attachments = payload.get('Attachments')
    if attachments:
        # sql expression to insert data into attachment table
        attachment_insertion = ("INSERT INTO attachment"
                "(attachment_hash, path_to_attachment_file, "
                "attachment_name, attachment_size, attachment_type, mail_id) "
                "VALUES (%s, %s, %s, %s, %s, %s)")
        # define payload keys which belongs to attachment table
        attachment_keys = ['md5', 'path to attachment', 'name', 'size', 'type']
        # insert each attachment into attachment table
        for attachment in attachments:
            attachment_params = [attachment.get(key) for key in attachment_keys]
            attachment_params.append(mail_id)
            logger.info("Executing inserting to attachment table")
            cursor.execute(attachment_insertion, attachment_params)

@db_connection
def data_selection(cnx, mail_id = None):
    # Function which is selecting rows from db
    # Select only rows for 1 email if mail_id is defined
    # Args:
    #    cnx - opened MySQLdb connection
    #    mail_id(int) - select only rows for email with mail_id
    # Returns:
    #    mail_rows(dict) - dictionary with all joined tables
    # define cursor with dictionary type
    cursor = cnx.cursor(MySQLdb.cursors.DictCursor)
    sql =("SELECT * FROM metadata LEFT "
          "JOIN attachment ON (metadata.mail_id = attachment.mail_id) "
          "JOIN mail_to ON (mail_to.mail_id=metadata.mail_id)")
    if mail_id:
        sql+= "WHERE metadata.mail_id = %s" % (mail_id, )
        logger.debug("selecting emeil with id %s" % (mail_id, ))
    cursor.execute(sql)
    mail_rows = cursor.fetchall()
    return mail_rows

@db_connection
def id_selection(cnx):
    # Selecting list of email ids in database
    # Args:
    #    cnx - opened MySQLdb connection
    # Returns:
    #   mail_ids(list) - email ids list
    cursor = cnx.cursor()
    sql =("SELECT mail_id FROM metadata")
    logger.info("Selecting mail ids")
    cursor.execute(sql)
    ids = cursor.fetchall()
    mail_ids = []
    for mail_id in ids:
        mail_ids.append(mail_id[0])
    return mail_ids

@db_connection
def delete_mail(cnx, mail_id):
    # Deleting mail with having it id from db
    # Args:
    #    cnx - opened MySQLdb connection
    #    mail_id(int) - id of email to delete
    # Returns:
    #   result:
    #    True if email was deleted
    #    False if email didn't exist
    result = False
    cursor = cnx.cursor()
    sql =("DELETE FROM metadata WHERE mail_id =%s" % mail_id)
    logger.info("Deleting mail with id %s" % (mail_id, ))
    deleting_result = cursor.execute(sql)
    if deleting_result:
        result = True
    logger.debug("Result of deleting %s" % (result, ))
    return result

@db_connection
def update_mail(cnx, mail_id, to_update):
    # Updating mail with having it id in database
    # Args:
    #    cnx - opened MySQLdb connection
    #    mail_id(int) - id of email to update
    #    to_update(dict) - dictionary of values that will be updated
    # Returns:
    #    result:
    #     True if email was updated
    #     False if not
    result = False
    cursor = cnx.cursor()
    set_expression  = ",".join(["%s=%s" % (key, '%s') for key in to_update.keys()])
    sql = "UPDATE metadata SET %s WHERE mail_id = %s" % (set_expression, mail_id)
    params = (to_update.values())
    logger.info("Updating mail with id %s" % (mail_id, ))
    updating_result = cursor.execute(sql, params)
    if updating_result:
        result = True
    logger.debug("result of updating is %s" % (result, ))
    return result

@db_connection
def select_attachment(cnx, at_id):
    # Selecting from attachment table 
    # Args:
    #    cnx - opened MySQLdb connection
    #    at_id(int) - attachment id to select
    # Results:
    #    mail_rows(dict in tuple) - dictionary of all attachment raws
    cursor = cnx.cursor(MySQLdb.cursors.DictCursor)
    sql =("SELECT * FROM attachment "
          "WHERE attachment_id = %s" % at_id)
    logger.info("Selecting attachment with id %s" % (at_id, ))
    cursor.execute(sql)
    mail_rows = cursor.fetchall()
    return mail_rows

