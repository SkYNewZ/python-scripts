#!/usr/bin/python3.5

import requests
import smtplib
from email.mime.text import MIMEText
import logging
import argparse

KIMSUFI_URL = 'https://www.ovh.com/engine/api/dedicated/server/availabilities?country=fr'

# Don't forget to format the server name : MAIL_SUBJECT.format(MY_SERVER_NAME)
MAIL_SUBJECT = 'OVH Server Availability : {}'

# Main configurations
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S', level=logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument(
    '--server',
    help='Wich server to you search for availability',
    type=str,
    required=True
)
parser.add_argument(
    '--datacenter',
    help='Which preferred data center are you searching for',
    type=str,
    choices=['default', 'fra'],
    required=True
)
parser.add_argument(
    '--region',
    help='In which region are you searching for',
    type=str,
    choices=['europe'],
    required=True
)
parser.add_argument(
    '--host',
    help='SMTP host',
    required=True,
    type=str
)
parser.add_argument(
    '--port',
    help='SMTP port',
    required=True,
    type=int
)
parser.add_argument(
    '--user',
    help='SMTP user',
    required=True,
    type=str
)
parser.add_argument(
    '--password',
    help='SMTP password',
    required=True
)
parser.add_argument(
    '--sender',
    help='SMTP sender',
    required=False,
    default='python-scripts@lemairepro.fr'
)
parser.add_argument(
    '--target',
    help='Who will receive the mail',
    required=True,
    type=str
)
args = parser.parse_args()


def search_for_server_availability(server_name, prefered_datacenter, region_name):
    """
    Search availability if a given server (OVH reference code) in given data center and given region
    :param str server_name:
    :param str prefered_datacenter:
    :param str region_name:
    :return:
    """
    logging.info("Executing request : {}".format(KIMSUFI_URL))
    r = requests.get(KIMSUFI_URL).json()
    for element in r:
        # check for KS-8 server in Europe
        if element['hardware'] == server_name and element['region'] == region_name:
            for datacenter in element['datacenters']:
                if datacenter['datacenter'] == prefered_datacenter:
                    # check availability
                    return datacenter['availability'] != 'unavailable'


def send_mail(me, you, message, subject):
    """
    Send a mail
    :param str subject: Subject of mail
    :param str me: From who send the email
    :param str you: Who receive the email
    :param str message: Content of the mail
    :return:
    """
    logging.info('Sending mail to {} - {} - {}'.format(you, subject, message))

    # Create a text/plain message
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = you

    # Send the message via our own SMTP server.
    s = smtplib.SMTP(args.host, args.port)
    s.login(args.user, args.password)
    s.send_message(msg)
    s.quit()


if __name__ == '__main__':
    logging.info('Start searching with params : \n\t{}'.format(
        '\n\t'.join(['%s:: %s' % (key, value) for (key, value) in vars(args).items()])))
    response = search_for_server_availability(args.server, args.datacenter, args.region)
    if response:
        logging.info(args.server + ' found.')
        send_mail(me=args.sender,
                  you=args.target,
                  message='Purchase link : https://www.kimsufi.com/fr/commande/kimsufi.xml?reference=' + args.server,
                  subject=MAIL_SUBJECT.format(args.server))
        logging.info('Done.')
    else:
        logging.info(args.server + ' not found.')
        logging.info('Done.')
