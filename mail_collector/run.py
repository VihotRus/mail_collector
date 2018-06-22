#!/usr/bin/python

from flask import (Flask, render_template, jsonify, abort,
                make_response, request, flash, redirect, send_file)
from src.email_parser.email_parser import EmailPayload
from src.db import db, db_filtres
from src.config_init import logger
from argparse import ArgumentParser, RawTextHelpFormatter, SUPPRESS
from werkzeug.utils import secure_filename

# app init
app = Flask(__name__)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

@app.route("/", methods=['GET', 'POST'])
@app.route("/home/", methods=['GET', 'POST'])
def home_page():
    # Posting new messages and get home page
    if request.method == 'POST':
        logger.info("Posting new message")
        if 'file' not in request.files:
            flash('No file part')
            return redirect("/home/")
        mail_source = request.files['file']
        mail_name = secure_filename(mail_source.filename)
        mail = EmailPayload(mail_source, mail_name)
        logger.info("Starting to parse file")
        parsed_mail = mail.parsed_mail()
        if parsed_mail:
            logger.info("Message payload added to db")
            return make_response(jsonify("Mail added"), 201)
        else:
            flash('Not email')
            logger.info("File is not email")
            return redirect("/home/")
    elif request.method == 'GET':
        return render_template('home.html')

@app.route("/about/", methods=['GET'])
def about():
    return render_template('about.html', title= 'About')

@app.route("/mail_text/<int:mail_id>", methods=['GET'])
def get_mail_body(mail_id):
    # Return mail body if email is in database
    visible = db_filtres.show_body(mail_id)
    if visible is None:
        abort(404)
    return visible

@app.route('/mails/', methods=['GET'])
def upload_mail():
    logger.info("Getting user readable mails")
    mails = db_filtres.get_mails()
    return jsonify(mails)

@app.route("/mail_ids/", methods=['GET'])
def get_mails_ids():
    logger.info("Getting all email ids")
    ids = db.id_selection()
    return jsonify(ids)

@app.route("/get_attachment/<int:at_id>", methods=['GET'])
def get_attachment(at_id):
    attachment = db.select_attachment(at_id)
    if not attachment:
        abort(404)
    attachment = attachment[0]
    try:
        return send_file(
                attachment_filename=attachment.get('attachment_name'),
                filename_or_fp = attachment.get('path_to_attachment_file'),
                mimetype=attachment.get('attachment_type'),
                as_attachment = True)
    except IOError:
        return make_response("The file don't exist anymore", 404)
        logger.warning("file is not in current path anymore")

@app.route('/mails/<int:mail_id>', methods=['GET'])
def get_mail(mail_id):
    logger.info("Getting email with id %s" % (mail_id, ))
    mail = db_filtres.get_mail(mail_id)
    if len(mail) == 0:
        abort(404)
    return jsonify(mail)

@app.route('/mails/<int:mail_id>', methods=['PUT'])
def put_mail(mail_id):
    info_to_update = request.json
    if not info_to_update:
        abort(400)
    if info_to_update.get('mail_id'):
        abort(403)
    result = db_filtres.update_mail(mail_id, info_to_update)
    if not result:
        abort(404)
    return jsonify(result)

@app.route('/mails/<int:mail_id>', methods=['DELETE'])
def delete_mail(mail_id):
    result = db_filtres.delete_mail(mail_id)
    if not result:
        abort(404)
    return make_response(jsonify(result), 204)

@app.errorhandler(404)
def not_found(error):
    logger.warning("Not found 404")
    return make_response(jsonify({'error' : [404, 'Not found']}), 404)

@app.errorhandler(400)
def not_found(error):
    logger.warning("Bad response 400")
    return make_response(jsonify({'error' : [400, 'Bad response']}), 400)

@app.errorhandler(403)
def not_found(error):
    logger.warning("Forbidden to change email id 403")
    return make_response(jsonify({'error' : [403, 'Forbidden to change id']}), 403)

def args_parser():
    # Parsing command line arguments to run API
    parser = ArgumentParser(description='flask app configuration',
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-H', '--host',
                        metavar = 'host',
                        default='0.0.0.0',
                        help='Determine host to start flask API\n'
                             'by default 0.0.0.0')
    parser.add_argument('-p', '--port',
                        metavar = 'port',
                        default='5000',
                        help='Determine port to start flask API\n'
                             'by default 5000')
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help=SUPPRESS)
    return parser.parse_args()

if __name__ == "__main__":
    args = args_parser()
    logger.info("Starting running API")
    app.run(host=args.host, port=args.port, debug=args.debug)
