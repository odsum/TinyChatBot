import time


class BannedUser:
    """ Class representing a banned user. """

    def __init__(self, **kwargs):
        self.ban_id = kwargs.get('id', 0)
        self.nick = kwargs.get('nick', '')
        self.req_id = kwargs.get('req', 0)
        self.success = kwargs.get('success', False)
        self.account = kwargs.get('username', '')
        self.banned_by = kwargs.get('moderator', '')
        self.reason = kwargs.get('reason', '')


class User:
    """ Class representing a user. """

    def __init__(self, **kwargs):
        self.id = kwargs.get('handle')
        self.nick = kwargs.get('nick', '')
        self.account = kwargs.get('username', '')
        self.giftpoints = kwargs.get('giftpoints', 0)
        self.featured = kwargs.get('featured', False)
        self.subscription = kwargs.get('subscription', 0)
        self.session_id = kwargs.get('session_id', '')
        self.achievement_url = kwargs.get('achievement_url', '')
        self.avatar = kwargs.get('avatar', '')
        self.is_lurker = kwargs.get('lurker', False)
        self.is_mod = kwargs.get('mod', False)
        self.is_owner = kwargs.get('owner', False)
        self.is_broadcasting = False
        self.is_waiting = False
        #
        self.user_level = 5
        self.join_time = time.time()
        self.tinychat_id = None
        self.last_login = None
        self.last_msg = None
        self.msg_time = 0.0


class Users:
    """ Class for doing various user related operations. """

    def __init__(self):
        """
        Initialize the Users class.

        Creating a dictionary for users and one for banned users.
        """
        self._users = dict()
        self._banned_users = dict()

    @property
    def all(self):
        """
        Returns a dictionary of all the users.

        :return: A dictionary where the key is the user ID and the value is User.
        :rtype: dict
        """
        return self._users

    @property
    def mods(self):
        """
        Returns a list of all the moderators.

        :return: A list of moderator User.
        :rtype: list
        """
        _mods = []
        for user in self.all:
            if self.all[user].is_mod:
                _mods.append(self.all[user])
        return _mods

    @property
    def signed_in(self):
        """
        Returns a list of all signed in users.

        :return: A list of all the signed in User
        :rtype: list
        """
        _signed_ins = []
        for user in self.all:
            if self.all[user].account:
                _signed_ins.append(self.all[user])
        return _signed_ins

    @property
    def lurkers(self):
        """
        Returns a list of the lurkers.

        :return: A list of lurkers User.
        :rtype: list
        """
        _lurkers = []
        for user in self.all:
            if self.all[user].is_lurker:
                _lurkers.append(self.all[user])
        return _lurkers

    @property
    def norms(self):
        """
        Returns a list of all normal users, e.g users that are not moderators or lurkers.

        :return: A list of all normal User.
        :rtype: list
        """
        _regulars = []
        for user in self.all:
            if not self.all[user].is_mod and not self.all[user].is_lurker:
                _regulars.append(self.all[user])
        return _regulars

    @property
    def broadcaster(self):
        """
        Returns a list of all broadcasting users.

        :return: A list of all the broadcasting User.
        :rtype: list
        """
        _broadcasters = []
        for user in self.all:
            if self.all[user].is_broadcasting:
                _broadcasters.append(self.all[user])
        return _broadcasters

    def clear(self):
        """ Clear the user dictionary. """
        self._users.clear()

    def add(self, user_info):
        """
        Add a user to the user dictionary.

        :param user_info: User information data.
        :type user_info: dict
        :return: The user as User.
        :rtype: User
        """
        if user_info['handle'] not in self.all:
            self._users[user_info['handle']] = User(**user_info)
        return self.all[user_info['handle']]

    def delete(self, handle_id):
        """
        Delete a user from the user dictionary.

        :param handle_id: The id (handle) of the user to delete.
        :type handle_id: int
        :return: The User of the deleted user or None if the ID was not found.
        :rtype: User | None
        """
        if handle_id in self.all:
            user = self._users[handle_id]
            del self._users[handle_id]
            return user
        return None

    def search(self, handle_id):
        """
        Search the user dictionary by ID.

        This is the primary search method, since the user ID (handle) is
        present in all(?) user related events.

        :param handle_id: The ID of the user to find.
        :type handle_id: int
        :return: The User or None if not found.
        :rtype: User | None
        """
        if handle_id in self.all:
            return self.all[handle_id]
        return None

    def search_by_nick(self, nick):
        """
        Search the user dictionary by nick name.

        :param nick: The nick name of the user to search for.
        :type nick: str
        :return: The User or None if not found.
        :rtype: User | None
        """
        for user in self.all:
            if self.all[user].nick == nick:
                return self.all[user]
        return None

    def search_by_account(self, account):
        """
        Search the user dictionary by account.

        :param account: The accountof the user to search for.
        :type account: str
        :return: The User or None if not found.
        :rtype: User | None
        """
        for user in self.all:
            if self.all[user].account == account:
                return self.all[user]
        return None

    def search_containing(self, contains):
        """
        Search the user dictionary for nick names matching the search string.

        :param contains: The search string to search for in the nick names.
        :type contains: str
        :return: A list of User matching the search string.
        :rtype: list
        """
        _users_containing = []
        for user in self.all:
            if str(contains) in self.all[user].nick:
                _users_containing.append(self.all[user])
        return _users_containing

    # Banlist related.
    @staticmethod
    def _find_most_recent(user_obj_list):
        """
        Find the most recent banned user in a list of BannedUser objects.

        :param user_obj_list: A list containing BannedUser objects.
        :type user_obj_list: list
        :return: A BannedUser object or None.
        :rtype: BannedUser | None
        """
        _highest = 0
        _user_obj = None

        for user_obj in user_obj_list:
            if user_obj.ban_id > _highest:
                _highest = user_obj.ban_id
                _user_obj = user_obj

        return _user_obj

    @property
    def banlist(self):
        """
        Returns a dictionary of all banned users.

        :return: A dictionary where the key is the ban ID and the value is BannedUser.
        :rtype: dict
        """
        return self._banned_users

    @property
    def banned_users(self):
        """
        Returns a list of all the BannedUser objects.

        :return: A list containing BannedUser objects.
        :rtype: list
        """
        _banned_users = []
        for banned_user in self.banlist:
            _banned_users.append(self.banlist[banned_user])
        return _banned_users

    @property
    def banned_accounts(self):
        """
        Returns a list of BannedUser account name.

        :return: A list of BannedUser containing account name.
        :rtype: list
        """
        _accounts = []
        for ban_id in self.banlist:
            if self.banlist[ban_id].account:
                _accounts.append(self.banlist[ban_id])
        return _accounts

    @property
    def last_banned(self):
        """
        Returns the last BannedUser object.

        :return: The last BannedUser object from the banlist.
        :rtype: BannedUser | None
        """
        return self._find_most_recent(self.banned_users)

    def add_banned_user(self, ban_info):
        """
        Add a user to the banned user dictionary.

        :param ban_info: The banned user's ban information.
        :type ban_info: dict
        :return: A BannedUser.
        :rtype: BannedUser
        """
        # if not ban_info['id']:
        #     ban_info['id'] = 0
        if ban_info['id'] not in self.banlist:
            self._banned_users[ban_info['id']] = BannedUser(**ban_info)
        return self.banlist[ban_info['id']]

    def delete_banned_user(self, ban_info):  # TODO: Maybe change this to delete by ban id only.
        """
        Delete a banned user from the banned user dictionary.

        :param ban_info: The banned user's ban information.
        :type ban_info: dict
        :return: The BannedUser or None if not in the dictionary.
        :rtype: BannedUser | None
        """
        if ban_info['id'] in self.banlist:
            banned_user = self.banlist[ban_info['id']]
            del self._banned_users[ban_info['id']]
            return banned_user
        return None

    def clear_banlist(self):
        """ Clear the ban list. """
        self._banned_users.clear()

    def search_banlist(self, ban_id):
        """
        Search the banlist dictionary by ban ID.

        :param ban_id: The ban ID to search for.
        :type ban_id: int
        :return: A BannedUser or None if not found.
        :rtype: BannedUser | None
        """
        if ban_id in self.banlist:
            return self.banlist[ban_id]
        return None

    def search_banlist_by_nick(self, user_name):
        """
        Search the banlist for a username.

        If more than one username match is found,
        then the most recent BannedUser object will be returned.

        :param user_name: The user name of the banned user to search for.
        :type user_name: str
        :return: A BannedUser object or None if no match was found in the banlist.
        :rtype: BannedUser | None
        """
        _candidates = []
        for ban_id in self.banlist:
            if self.banlist[ban_id].nick == user_name:
                _candidates.append(self.banlist[ban_id])

        if len(_candidates) == 0:
            return None

        return self._find_most_recent(_candidates)

    def search_banlist_containing(self, contains):
        """
        Search the banlist for user names matching the search str.

        :param contains: The search term to search for.
        :type contains: str
        :return: A list of matches.
        :rtype: list
        """
        _banned_containing = []
        for user in self.banlist:
            if str(contains) in self.banlist[user].nick:
                _banned_containing.append(self.banlist[user])
        return _banned_containing

    def search_banlist_by_req_id(self, req_id):
        """
        Search the banned user dictionary by req ID.

        :param req_id: The req ID to search for.
        :type req_id: int
        :return: A BannedUser matching the req ID or None if not found.
        :rtype: BannedUser | None
        """
        for ban_id in self.banlist:
            if self.banlist[ban_id].req_id == req_id:
                return self.banlist[ban_id]
        return None
