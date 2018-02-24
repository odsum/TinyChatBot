# PickleDB Wrapper class by Nortxort (https://github.com/nortxort)
# Molested by odsum (https://github.com/odsum)
# 2.12.18
# Honoured to work with Nortxort since his bot is why I started playing with python.


import os
import time
import pickledb


def find_list_index(a_list, item):
    """
    Finds the index of an item in a list.

    :param a_list: A list to find the index in.
    :type a_list: list
    :param item: The item to find the index for.
    :type item: str
    :return: The index of the item, or None if not in the list.
    :rtype: int | None
    """
    if item in a_list:
        for i, value in enumerate(a_list):
            if value == item:
                return i


class DataBase:
    """ Pickledb wrapper class. """

    def __init__(self, file_name, file_path='', load=False):
        """
        Initialize the DataBase class.

        :param file_name: The name of the database file without extension.
        :type file_name: str
        :param file_path: The path to the database file. Should end with /
        :type file_path: str
        :param load: Load the database file at class initialization.
        :type load: bool
        """
        self.file_name = '{0}.db'.format(file_name)
        self.file_path = file_path
        self._db = None

        if load:
            self.load()

    @property
    def db(self):
        """
        Returns the pickledb database instance.

        :return: pickledb instance.
        :rtype: pickledb | None
        """
        return self._db

    @property
    def users(self):
        """
        Returns a dictionary of all the users in the database.

        The key will be account name and the
        value is a dictionary containing user data

        :return: A dictionary of all the users.
        :rtype: dict
        """
        return self._db.dgetall('users')

    @property
    def word_bans(self):
        """
        Returns a list of the word bans.

        :return: A list of ban words.
        :rtype: list
        """
        return self._db.lgetall('word_bans')

    @property
    def nick_bans(self):
        """
        Returns a list of the nick bans.

        :return: A list of ban nicks.
        :rtype: list
        """
        return self._db.lgetall('nick_bans')

    @property
    def account_bans(self):
        """
        Returns a list of the account bans.

        :return: A list of ban accounts.
        :rtype: list
        """
        return self._db.lgetall('account_bans')

    def has_db_file(self):
        """
        Check that the given database file name exists at the given path.

        :return: True if the file was found, else False.
        :rtype: bool
        """
        if os.path.isfile(self.file_path + self.file_name):
            return True
        return False

    def create_db_path(self):
        """
        Creates the path to the database file should it not exists.

        :return: True if the path was created, else False.
        :rtype: bool
        """
        if self.file_path != '':
            if not os.path.exists(self.file_path):
                os.makedirs(self.file_path)
                return True
        return False

    def create_defaults(self):
        """
        Create database defaults.
        """
        if self._db is None:
            self.load()

        self._db.dcreate('users')  # dict
        self._db.dcreate('tickets')  # dict
        self._db.lcreate('word_bans')  # list
        self._db.lcreate('nick_bans')  # list
        self._db.lcreate('account_bans')  # list

        self._db.dump()

    def load(self):
        """
        Load or reload the database file.
        """
        if self.file_name is None or self.file_name == '':
            raise Exception('Missing file name, file_name=%s', self.file_name)
        else:
            self._db = pickledb.load(self.file_path + self.file_name, False)

    def dump(self):
        """
        Dump the database data to file.
        """
        self._db.dump()

    def extend_list(self, list_name, a_list):
        """
        Extend a database list.

        :param list_name: The name of the list in the database.
        :type list_name: str
        :param a_list: A list to extend the existing list with.
        :type a_list: list
        """
        self._db.lextend(list_name, a_list)
        self._db.dump()

    def add_user(self, account, level, reason='', greet=''):
        """
        Add a user to the database.

        Maybe this should return the added user?

        :param account: The account of the user.
        :type account: str
        :param level: The level of the user.
        :type level: int
        :param reason:
        :type reason: str
        :param greet:
        :type greet: str
        """
        _data = {
            'level': level,
            'reason': reason,
            'account': account,
            'greet': greet,
            'ts': int(time.time())
        }
        self._db.dadd('users', (account, _data))
        self._db.dump()

    def remove_user(self, account):
        """
        Remove a user from the database.

        :param account: The account of the user.
        :type account: str
        :return: The removed user.
        :rtype: dict
        """
        _user = None
        if self._db.dexists('users', account):
            _user = self._db.dpop('users', account)
            self._db.dump()
        return _user

    def add_ticket(self, account, score, nick, reason=''):
        """
        Add a spam ticket to the database.

        :param account: The account of the user if available.
        :type account: str
        :param score: The score of spam for the offense.
        :type score: int
        :param reason:
        :type reason: str
        :param nick: The nick of the user.
        :type reason: str
        """
        _data = {
            'score': score,
            'reason': reason,
            'account': account,
            'ts': int(time.time())
        }
        self._db.dadd('tickets', (nick, _data))
        self._db.dump()

    def find_db_user(self, account):
        """
        Find a user in the database.

        :param account: The account of the user to find.
        :type account: str
        :return: A dictionary containing the user data, or None if not found.
        :rtype: dict
        """
        if account in self.users:
            return self.users[account]
        return None

    def find_db_ticket(self, nick):
        """
        Find a nick in a ticket in the database.

        :param nick: The nick in ticket.
        :type nick: str
        :return: A dictionary containing the ticket data, or None if not found.
        :rtype: dict
        """
        if self.db.dexists('tickets', nick):
            ticket = self.db.dget('tickets', nick)
            return ticket
        else:
            return 0

    def find_db_word_bans(self, word):
        """
        Find a badword in the database.

        :param word: The banned word to find.
        :return: True/False
        :rtype: dict
        """
        if word in self.word_bans:
            return True
        return None

    def find_db_nick_bans(self, nick):
        """
        Find a nick in the database.

        :param nick: The banned nick.
        :return: True/False
        :rtype: dict
        """
        if nick in self.nick_bans:
            return True
        return None

    def find_db_account_bans(self, account):
        """
        Find an account in the database.

        :param account: The banned.
        :type account: str
        :return: True/False
        :rtype: dict
        """
        if account in self.account_bans:
            return True
        return None

    def add_bad_word(self, word):
        """
        Add a word to the word bans database list.

        :param word: The word to add to the database list.
        :type word: str
        """
        self._db.ladd('word_bans', word)
        self._db.dump()

    def remove_bad_word(self, word):
        """
        Remove a word from the word bans database list.

        :param word: The word to remove from the database list.
        :type word: str
        :return: The index on the list.
        :rtype: int | None
        """
        _index = find_list_index(self.word_bans, word)
        if _index is not None:
            self._db.lpop('word_bans', _index)
            self._db.dump()
            return _index
        return None

    def add_bad_nick(self, nick):
        """
        Add a bad nick to the nick bans database list.

        :param nick: The nick to add to the list.
        :type nick: str
        """
        self._db.ladd('nick_bans', nick)
        self._db.dump()

    def remove_bad_nick(self, nick):
        """
        Remove a nick from the nick bans database list.

        :param nick: The nick to remove from the database list.
        :type nick: str
        :return: The index on the list.
        :rtype: int | None
        """
        _index = find_list_index(self.nick_bans, nick)
        if _index is not None:
            self._db.lpop('nick_bans', _index)
            self._db.dump()
            return _index
        return None

    def add_bad_account(self, account):
        """
        Add an account to the account bans database list.

        :param account: The account to add to the account bans database list.
        :type account: str
        """
        self._db.ladd('account_bans', account)
        self._db.dump()

    def remove_bad_account(self, account):
        """
        Remove an account from the account bans database list.

        :param account: The account to remove from the database list.
        :type account: str
        :return: The index on the list.
        :rtype: int | None
        """
        _index = find_list_index(self.account_bans, account)
        if _index is not None:
            self._db.lpop('account_bans', _index)
            self._db.dump()
            return _index
        return None
