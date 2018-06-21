#!/usr/bin/python

# db_filtres module which is filtring information from db selection
# and shows user readable information

import os
import shutil
from src.config_init import logger
from src.db import db

def update_mail(mail_id, items_to_update):
    # Function to mail updating
    # Args:
    #    mail_id(int) - id of email to update
    #    items_to_update(dict) - dict from PUT method of items to update
    # Returns:
    #    result(dict) - returns dictionary which can have keys:
    #       Wrong keys - if some metadata raws were uncorrect they will add to
    #                    Wrong keys and not will be updated
    #       Updated - info about updated items
    #       Error - shows error if it was occured
    logger.debug("Updating email with items %s" % (items_to_update, ))
    result = {}
    checked = key_checker(items_to_update)
    not_updated = checked.get('impossible_keys')
    if not_updated:
        result["Wrong keys"] = not_updated
        logger.debug("wrong keys %s" % (not_updated, ))
    to_update = checked.get('possible_keys')
    if to_update:
        to_update_formatted = key_reformatter(to_update)
        logger.debug("updating %s" % (to_update_formatted, ))
        updating_result = db.update_mail(mail_id, to_update_formatted)
        if updating_result is True:
            result["Updated"] = to_update
            logger.debug("Updated %s" % (to_update, ))
        elif updating_result:
            result["Error"] = updating_result
            logger.warning("error occured %s" % (updating_result, ))
    return result


def key_checker(to_check):
    # This function is checking keys of recieved dictionary
    # that can be updated
    # Args:
    #    to_check(dict) - recieved dictionary of items to update
    # Returns:
    #    result(dict) - dictionary with possible and impossible keys to update
    logger.info("Checking keys to update")
    possible_keys = ['date', 'from', 'subject']
    impossible = []
    for key in to_check.keys():
        if key not in possible_keys:
            impossible.append(key)
            del to_check[key]
    result = {
            'possible_keys' : to_check,
            'impossible_keys' : impossible
            }
    logger.debug("Checked %s" % (result, ))
    return result

def key_reformatter(dict_to_change):
    # This function is reformating keys that were requested by user
    # to keys that might been changed in database
    # Args:
    #   dict_to_change(dict) - dictionary with user keys
    # Returns:
    #    formatted_dict(dict) - dictionary of database keys to update
    logger.info("Reformatting leys to update")
    formatted_keys = {
        'date' : 'mail_date',
        'from' : 'mail_from',
        'subject' : 'mail_subject'
            }
    formatted_dict = {}
    for key, value in dict_to_change.items():
        formatted_dict[formatted_keys[key]] = value
    logger.debug("Reformated keys %s" % (formatted_dict, ))
    return formatted_dict

def get_mails():
    # This function returns list of mails formatted to user
    # Returns:
    #    list_of_mails(list)  - list of reformatted mails
    logger.info("Getting mails from db")
    mails = db.data_selection()
    list_of_mails = []
    parts = {}
    logger.info("Creating dictionary with mail_id's")
    for mail in mails:
        part = parts.get(mail.get('mail_id'))
        if part:
            part.append(mail)
        else:
            part = [mail]
        parts[mail.get('mail_id')] = part
    for part in parts.values():
        email = mail_modification(part).get('for_user')
        list_of_mails.append(email)
    return list_of_mails

def get_mail(mail_id):
    # this function return user shown email if it exists
    # Args:
    #    mail_id(int) - id of email to select
    # Returns:
    #    modified_mail(dict) - user readable email
    logger.info("Getting mail from id %s" % (mail_id, ))
    mail = db.data_selection(mail_id)
    modified_mail = mail_modification(mail).get('for_user')
    if not modified_mail.get("mail_id"):
        modified_mail = ''
    return modified_mail

def mail_modification(mail):
    # This function modificate email raws from database to user readable email
    # Args:
    #    mail - raws from db selection
    # Returns:
    #    modified_email(dict) - dictionary with 2 keys:
    #      for_user - email items to show user
    #      hidden - pathes to original files for deleting function
    logger.info("Modificating email to user show")
    email_items = {'Attachments' : [], 'Recipients' : [], 'Metadata' : {}}
    hidden_items = {'Attachments' : [], 'Metadata' : {}}
    for part in mail:
        if part.get('attachment_id'):
            logger.info("Modificating attachment showwing")
            attachment = {
                    'id' : part.get('attachment_id'),
                    'md5' : part.get('attachment_hash'),
                    'name' : part.get('attachment_name'),
                    'size' : part.get('attachment_size'),
                    'type' : part.get('attachment_type'),
                    }
            attachment_hidden = {
                    'path_to_attachment' : part.get('path_to_attachment_file'),
                    }
            if attachment not in email_items['Attachments']:
                email_items['Attachments'].append(attachment)
                hidden_items['Attachments'].append(attachment_hidden)
        logger.info("Modificating recipient showwing")
        recipient={
                'to' : part.get('mail_recipient')
                }
        if recipient not in email_items['Recipients']:
            email_items['Recipients'].append(recipient)
        logger.info("Modificating metadata showwing")
        email_items['mail_id'] = part.get('mail_id')
        email_items['Metadata']['from'] = part.get('mail_from')
        email_items['Metadata']['subject'] = part.get('mail_subject')
        email_items['Metadata']['date'] = part.get('mail_date')
        hidden_items['Metadata']['path_to_html'] = part.get('path_to_html_body')
        hidden_items['Metadata']['path_to_text'] = part.get('path_to_text_body')
        hidden_items['Metadata']['path_to_original'] = part.get('path_to_original')
    modified_email = {
            'for_user' : email_items,
            'hidden' : hidden_items
            }
    return modified_email

def delete_mail(mail_id):
    # This checking if email exists and calls 
    # functions to delete it from db and NFS
    # Args:
    #    mail_id(int) - id of email to delete
    # Returns:
    #    result(dict) - empty dictionary if email didn't exist
    #        Deleted - message with deleted mail_id
    #        Error - if error occured
    logger.info("Deleting mail with id %s" % (mail_id, ))
    result = {}
    mail = db.data_selection(mail_id)
    if mail:
        deleting_result = db.delete_mail(mail_id)
        if deleting_result is True:
            result['Deleted'] = "Mail with id %s" % (mail_id, )
            delete_mail_files(mail)
            logger.debug("Mail with %s deleted" % (mail_id, ))
        elif deleting_result:
            result['Error'] = deleting_result
            logger.warning("Error occured %s" % (deleting_result, ))
    return result

def delete_mail_files(mail):
    # This function deleting mail files from NFS
    # Args:
    #    mail - mail rows from database

    # get email pathes from mail raws and delete them
    logger.info("Starting to delete files from NFS")
    mail_to_delete = mail_modification(mail).get('hidden')
    for mail_part in mail_to_delete.keys():
        if mail_part == 'Metadata':
            for value in mail_to_delete[mail_part].values():
                try:
                    file_dir = os.path.dirname(value)
                except AttributeError:
                    break
                if os.path.isdir(file_dir):
                    shutil.rmtree(file_dir)
                    logger.debug("Deleted directory %s" % (file_dir, ))
        if mail_part == 'Attachments':
            for attachment in mail_to_delete[mail_part]:
                for attachment_location in attachment.values():
                    try:
                        file_dir = os.path.dirname(attachment_location)
                    except AttributeError:
                        break
                    if os.path.isdir(file_dir):
                        shutil.rmtree(file_dir)
                        logger.debug("Deleted directory %s" % (file_dir, ))

def show_body(mail_id):
    # Return email's body
    # Args:
    #  mail_id(int) - id of email which body need to be returned
    # Returns:
    #    visible - return empty string if no email with this id
    #              return informative message if file doesn't axist anymore
    #              return email's html body if it exists
    #              else return text body of email
    logger.info("Starting body showwing")
    mail = db.data_selection(mail_id)
    if len(mail) == 0:
        visible = ""
    else:
        html_path = mail[0].get('path_to_html_body')
        if html_path:
            try:
                with open(html_path, 'r') as path_to_html:
                    visible = path_to_html.read()
            except IOError as error:
                logger.error(error)
                return "The file don't exist anymore"
        else:
            text_path = mail[0].get('path_to_text_body')
            try:
                with open(text_path, 'r') as path_to_text:
                    visible = path_to_text.read()
            except IOError as error:
                logger.error(error)
                return "The file don't exist anymore"
    return visible
