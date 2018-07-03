from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools


class GmailApp:
    """
    Class for using Gmail API
    https://developers.google.com/resources/api-libraries/documentation/gmail/v1/python/latest/index.html
    """

    def __init__(self, scopes=None, stored_credentials='credentials.json', key_file='client_secret.json'):
        """
        Init the Gmail service
        :param scopes: Authorized scopes
        :param stored_credentials: Credentials used for the refresh, after first init
        :param key_file: Main credentials from https://console.developers.google.com/apis/credentials
        """
        if scopes is None:
            scopes = []
        store = file.Storage(stored_credentials)
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets(key_file, scopes)
            creds = tools.run_flow(flow, store)
        self.__service = build('gmail', 'v1', http=creds.authorize(Http()), cache_discovery=False)

    def get_gmail_connection(self):
        """
        :return: The current service
        """
        return self.__service

    def searchMessages(
            self,
            userId='me',
            labelIds=None,
            q=None,
            pageToken=None,
            maxResults=None,
            includeSpamTrash=None,
            fields=''
    ):
        """
        Search for messages https://developers.google.com/resources/api-libraries/documentation/gmail/v1/python/latest/gmail_v1.users.messages.html#list
        :param userId:
        :param labelIds:
        :param q:
        :param pageToken:
        :param maxResults:
        :param includeSpamTrash:
        :param fields:
        :return:
        """
        params = {}
        params['userId'] = userId
        params['labelIds'] = labelIds
        params['q'] = q
        params['pageToken'] = pageToken
        params['maxResults'] = maxResults
        params['includeSpamTrash'] = includeSpamTrash
        params['fields'] = fields
        return self.__service.users().messages().list(**params).execute()

    def deleteMessages(self, ids, userId='me'):
        """
        Delete messages https://developers.google.com/resources/api-libraries/documentation/gmail/v1/python/latest/gmail_v1.users.messages.html#batchDelete
        :param ids: List if messages id
        :param userId: User
        :return:
        """
        if not isinstance(ids, list):
            raise ValueError('Ids should be a list of id')
        else:
            body = {}
            body['ids'] = ids
            return self.__service.users().messages().batchDelete(userId=userId, body=body).execute()

    def trashMessages(self, messageId, userId='me'):
        """
        Trash messages https://developers.google.com/resources/api-libraries/documentation/gmail/v1/python/latest/gmail_v1.users.messages.html#trash
        :param messageId: list or one message id
        :param userId: User
        :return:
        """
        if isinstance(messageId, list):
            for m in messageId:
                self.__service.users().messages().trash(userId=userId, id=m).execute()
            return True
        else:
            return self.__service.users().messages().trash(userId=userId, id=messageId).execute()
