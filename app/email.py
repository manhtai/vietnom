from threading import Thread
from flask import current_app, render_template
from flask.ext.mail import Message
from app import mail, celery


#############################################################################
# Using Celery (For big web)
#############################################################################

@celery.task
def send_async_email(msg):
    mail.send(msg)

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=(app.config['MAIL_SENDER'],\
                          app.config['MAIL_USERNAME']), 
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    send_async_email.delay(msg)




#############################################################################
# Using Thread (For small web)
#############################################################################

def send_async_email_thread(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email_thread(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=(app.config['MAIL_SENDER'],\
                          app.config['MAIL_USERNAME']), 
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    thr = Thread(target=send_async_email_thread, args=[app, msg])
    thr.start()
    return thr


