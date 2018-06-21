-=============================================================================-

         Email Collector Application Programming Interface
-=============================================================================-

This application was designed to parse uploaded emails and store such information in the database as Sender, Recipients, Subject, Body (text/plain), Body (text/html), Timestamp, Attachments (name, size, type, MD5, path to saved file on the server).
User is able to upload emails through this API, read, update and delete them.
Also, downloading back saved attachments and uploaded early entire emails supported.

-=============================================================================-

How to install and run the application:

-=============================================================================-

1.Install requirements:
$ pip install -r requirements.txt

2.Make run.py file executable:
$ chmod +x run.py

3.Create 'email_collector' database structure:
$ cd db

mysql> source create_db.sql

4.Export enviroment variables
export PROD_ROOT=path_to_api_location_directory
export CONF_ROOT=$PROD_ROOT/etc

5.Run the API:

./run.py -h usage: run.py [-h] [-H HOST] [-P PORT]

optional arguments: -h, --help show this help message and exit -H HOST, --host HOST Hostname for the Flask application -P PORT, --port PORT Port for the Flask application

Also, a hidden argument can be used:

--debug

$ ./run.py --host=0.0.0.0 --port=5000 --debug

-=============================================================================-

How to use the application. Supported features.

-=============================================================================-

Upload emails.
/
/home/ - methods GET/POST:

curl -X POST localhost:5000/home/ -F 'file=@/filename' -i

Retrieve uploaded emails.
/mails/ - method GET:

curl -i -X GET localhost:5000/mails/

Retrieve uploaded email by id.

/mails/id - method GET.

curl -i GET localhost:5000/mails/id

Update uploaded email.
/mails/id - method PUT:

curl -i -H 'Content-Type: application/json' -X PUT -d '{"date": "1", "subject": "text"}' localhost:5000/mails/id

Delete uploaded email. All related saved attachments and source email file will be deleted as well.
/mails/id - method DELETE:

curl -i curl -X DELETE localhost:5000/mails/id

Download attachment from server.
/get_attachment/id - method GET:

curl -i GET localhost:5000/get_attachment/id

Retrieve email body
/mail_text/id - method GET:

curl -i GET localhost:5000/mail_text/id

Retrieve ids of all emails in server
/mail_ids/ - method GET

curl -i GET localhost:5000/mail_ids/

