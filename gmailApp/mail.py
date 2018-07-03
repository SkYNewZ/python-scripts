class Mail:
    def __init__(self, mailObject):
        self.id = mailObject['id']
        self.threadId = mailObject['threadId']
        self.labelIds = mailObject['labelIds']
        self.snippet = mailObject['snippet']

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)
