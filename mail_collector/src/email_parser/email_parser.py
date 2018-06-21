#!/usr/bin/python

# email_parser module describes message class
#   which is parsing original messages
import time
import os
import uuid
import md5
from email import message_from_file
from email.header import decode_header
from email.utils import parseaddr
from dateutil.parser import parse
from src.db.db import data_insertion_mysql
from src.config_init import config, ENV_DIR, logger

# Initializating pathes to save
# original msgs, bodies and attachments from config
SAVING_SECTION = 'data_save'
ORIGINALS_DIR = config.get(SAVING_SECTION, 'original_dir')
ATT_DIR = config.get(SAVING_SECTION, 'att_dir')
BODY_DIR = config.get(SAVING_SECTION, 'body_dir')

# Joining enviroment directory with saving pathes
ORIGINALS_DIR = os.path.join(ENV_DIR, ORIGINALS_DIR)
ATT_DIR = os.path.join(ENV_DIR, ATT_DIR)
BODY_DIR = os.path.join(ENV_DIR, BODY_DIR)

class EmailPayload(object):
    # Class which is accepting original message file and it's name
    #   and has method parsed_mail which returns mail payload
    #   with metadata and attachments
    def __init__(self, original_file, file_name):
        # Initializating original message file and it's name
        #    initializating saving directories
        #    generate sub directory for every message instance
        # Args:
        #    original_file(open file object) - original msg file
        #    file_name(str) - name of file
        logger.debug("Initializating EmailPayload class object")
        self.original_file = original_file
        self.file_name = file_name
        self.sub_dir = str(uuid.uuid4())
        self.original_dir = ORIGINALS_DIR
        self.original_dir = os.path.join(self.original_dir, self.sub_dir)
        self.body_dir = BODY_DIR
        self.body_dir = os.path.join(self.body_dir, self.sub_dir)
        self.att_dir = ATT_DIR
        self.att_dir = os.path.join(self.att_dir, self.sub_dir)
        # define empty attachment list
        self.attachments = []

    def parsed_mail(self):
        # Method which returns parsed mail payload
        #   saving attachments, original message and bodies
        #   and insert metadata into database
        #   Returns:
        #    email dictionary payload with parsed metadata
        #    empty dictionary if parsed object is not email

        # Getting email.message.Message object from original file
        self.mail = message_from_file(self.original_file)
        logger.info("Getting mail.message.Message object from binary file")
        # Define email metadata
        self.mail_payload = {}
        # Check if recieved email.message.Message is mail
        if self.is_mail(self.mail):
            # creating directory to save original file
            os.makedirs(self.original_dir)
            logger.info("Created directory for original file")
            # saving original file
            self.original_path = os.path.join(self.original_dir, self.file_name)
            self.object_write(self.original_path, str(self.mail))
            self.mail_payload['Original'] = self.original_path
            # calls method to get email metadata
            logger.debug("Calling self.get_mail_parts method to parse mail")
            self.get_mail_parts(self.mail)
            # insert metadata in mysql
            logger.debug("Calling data_insertion_mysql func "
                         "to insert %s" % (self.file_name, ))
            data_insertion_mysql(self.mail_payload)
        else:
            logger.info("The file %s is not email" % (self.file_name, ))
        return self.mail_payload

    def is_mail(self, mail):
        # Checking if received email.message.Message object is email
        #   Args:
        #    mail(email.message.Message) - Message class object to parse
        # Returns:
        #    True if mail is original email message file with headers
        #    False if not
        is_mail = False
        # message required headers
        checker = {'received', 'subject', 'message-id', 'date', 'from'}
        # checking if email.message.Message object has all
        # required headers
        keys = set([key.lower() for key in mail.keys()])
        if checker.issubset(keys):
            is_mail = True
        return is_mail

    def get_mail_parts(self, mail):
        # Calls methods to parse headers, body and attachments
        # Args:
        #    mail(email.message.Message) - message to parse
        logger.info("starting to parse mail")
        self.header_parse(mail)
        logger.info("starting parse body")
        logger.info("starting parse attachments")
        # running through mail parts
        # and adding attachments and body to the payload
        for part in mail.walk():
            self.parse_body(part)
            self.parse_att(part)
        logger.info("end with body parsing")
        logger.info("End with attachment parsing")

    def header_parse(self, mail):
        # Method which is parsing email headers
        # Args:
        #    mail(email.message.Message) - message to parse
        # get message header FROM
        logger.info("parsing headers of email")
        mail_from = parseaddr(mail.get('From'))[1]
        self.mail_payload['FROM'] = mail_from
        # get message header TO
        mail_to = mail.get('to')
        if mail_to is None:
            mail_to = mail.get('Delivered-To')
        mail_to = mail_to.split(',')
        for index, item in enumerate(mail_to):
            mail_to[index] = parseaddr(item)[1]
        self.mail_payload['TO'] = mail_to
        # get message subject
        subject = self.get_decoded(mail.get('subject'))
        if len(subject) == 0:
            subject = '(NO subject)'
        self.mail_payload['Subject'] = subject
        # get message date
        date = mail.get('date')
        datetime = parse(date)
        date_timestamp = int(time.mktime(datetime.timetuple()))
        self.mail_payload['Date'] = date_timestamp
        logger.debug("parsed headers in payload %s" % (self.mail_payload, ))

    def parse_body(self, part):
        # Method that is parsing email body
        # Args:
        #    part(1 element of email.message.Message.walk() func)

        # create directory to save bodies
        if not os.path.exists(self.body_dir):
            os.makedirs(self.body_dir)
            logger.info("created directory to save body")
        # saving text/plain body
        if part.get_content_type() == "text/plain":
            logger.info("mail has text body")
            text_body = part.get_payload(decode=True)
            text_body_path = os.path.join(self.body_dir, 'text')
            self.object_write(text_body_path, text_body)
            self.mail_payload['Text body'] = text_body_path
        # saving text/html body
        elif part.get_content_type() == "text/html":
            logger.info("mail has html body")
            html_body = part.get_payload(decode=True)
            html_body_path = os.path.join(self.body_dir, 'html')
            self.object_write(html_body_path, html_body)
            self.mail_payload['Html body'] = html_body_path

    def parse_att(self, part):
        # Method that is parsing email attachments
        # Args:
        #    part(1 element of email.message.Message.walk() func)

        # get filename of mail part, the name is None if not attachment
        att_name = part.get_filename()
        # check if email part is attachment
        if att_name:
            att_name = self.get_decoded(att_name)
            # creating directory to save attachments
            if not os.path.exists(self.att_dir):
                os.makedirs(self.att_dir)
                logger.info("created directory to save attachments")
            att_path = os.path.join(self.att_dir, att_name)
            # getting binary attachment file
            file_obj =  part.get_payload(decode=True)
            # saving binary attachment file
            self.object_write(att_path, file_obj)
            # getting attachment metadata
            # md5 hash code
            m = md5.new()
            m.update(file_obj)
            attachment_md5 = m.hexdigest()
            # attachment size
            attachment_size = os.path.getsize(att_path)
            # attachment type
            attachment_type = part.get_content_type()
            # creating dictionary with attachment metadata
            attachment = {
                        'path to attachment' : att_path,
                        'md5' : attachment_md5,
                        'size' : attachment_size,
                        'type' :  attachment_type,
                        'name' : att_name
                        }
            logger.info("created attachment payload")
            # adding attachment to attachment list
            self.attachments.append(attachment)
            logger.info("adding attachment to attachment list")
        # adding attachment list to mail payload
        self.mail_payload['Attachments'] = self.attachments

    def object_write(self, file_path, file_object):
        # Method for writing files
        # Args:
        #    file_path(str) - path to write
        #    file_object - file object to be written
        with open(file_path, 'w') as file_to_write:
            file_to_write.write(file_object)
        logger.debug("Saved file to %s" % (file_path, ))

    def get_decoded(self, header_to_decode):
        # Method for decoding subject and attachment names
        # Args:
        #    header_to_decode - email header to decode
        logger.debug("Header to decode - %s" % (header_to_decode, ))
        try:
            decoded = decode_header(header_to_decode)[0][0]
        except UnicodeError:
            decoded = header_to_decode
        logger.debug("Decoded header - %s" % (decoded, ))
        return decoded
