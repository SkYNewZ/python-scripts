#!/usr/bin/python

from gmail_client import GmailApp
import sys
import logging.handlers
import argparse

# Setup the Gmail API
SCOPES = 'https://mail.google.com/'
MAX_RESULTS = 100

parser = argparse.ArgumentParser(
    description='Tools for mass deleting mails',
    formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument(
    '--search',
    required=True,
    help='Search filter like on Gmail search bar'
)

parser.add_argument(
    '--mode',
    required=False,
    default='trash',
    help='Trash messages or delete definitively. Usage: --mode=trash or --mode=delete. Default: trash'
)

args = parser.parse_args()

logging.basicConfig(
    level='INFO',
    format='%(levelname)s %(filename)s %(message)s',
    datefmt='%H:%M:%S'
)

logging.info('*** Start on Python %s with %s ***', sys.version, args.search)


def main():
    gmail_service = GmailApp(scopes=SCOPES, stored_credentials='credentials.json', key_file='client_secret.json')

    # get list of email
    page_token = None
    while True:
        toDeleteArrayIds = []
        results = gmail_service.searchMessages(
            userId='me',
            labelIds=None,
            q=args.search,
            pageToken=page_token,
            maxResults=MAX_RESULTS,
            includeSpamTrash=None,
            fields='nextPageToken, messages'
        )

        mails = results.get('messages', [])
        page_token = results.get('nextPageToken')

        # get all ids
        for mail in mails:
            toDeleteArrayIds.append(mail['id'])

        # trigger the deletion for the current MAX_RESULTS mails
        if len(toDeleteArrayIds) > 0:
            if args.mode == 'delete':
                gmail_service.deleteMessages(toDeleteArrayIds, userId='me')
            else:
                gmail_service.trashMessages(toDeleteArrayIds, userId='me')
        if not page_token:
            break


if __name__ == '__main__':
    main()
