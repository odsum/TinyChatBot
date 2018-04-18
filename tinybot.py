# -*- coding: utf-8 -*-
"""
Buddybot by odsum (https://github.com/odsum)
Based off Tinybot by Nortxort (https://github.com/nortxort/tinybot-rtc)
"""

import logging
import threading
import time

import pinylib
from apis import youtube, other, locals_
from modules import register, welcome, spam, tokes, voting
from page import privacy
from util import tracklist, botdb

__version__ = '2.4.5'

log = logging.getLogger(__name__)


class TinychatBot(pinylib.TinychatRTCClient):
    musicicon = unicode("🎶", 'utf-8')
    warningicon = unicode("⚠", 'utf-8')
    notallowedicon = unicode("🚫", 'utf-8')
    nexticon = unicode("⏭", 'utf-8')
    playicon = unicode("▶", 'utf-8')
    radioicon = unicode("🔘", 'utf-8')
    lockicon = unicode("🔒", 'utf-8')
    unlockicon = unicode("🔓", 'utf-8')
    lockupicon = unicode("🔐", 'utf-8')
    micicon = unicode("🎙", 'utf-8')
    ballicon = unicode("🎱", 'utf-8')
    securityicon = unicode("🚨", 'utf-8')
    boticon = unicode("🤖", 'utf-8')
    cheersicon = unicode("🍻", 'utf-8')

    privacy_ = None
    timer_thread = None

    playlist = tracklist.PlayList()

    search_list = []
    is_search_list_yt_playlist = False
    bl_search_list = []

    dj_mode = 0
    djs = []
    cambans = []

    kick_pool = []
    ban_pool = []
    worker_kicks_working = False
    worker_bans_working = False

    tmp_announcement = None

    @property
    def config_path(self):
        """ Returns the path to the rooms configuration directory. """
        return pinylib.CONFIG.CONFIG_PATH + self.room_name + '/'

    def db_setup(self):
        self.buddy_db = botdb.DataBase('users', self.config_path)
        if not self.buddy_db.has_db_file():
            self.buddy_db.create_db_path()
            self.buddy_db.create_defaults()
            self.console_write(pinylib.COLOR['green'], '[DB] Created for %s' % self.room_name)

        self.buddy_db.load()
        self.console_write(pinylib.COLOR['green'], '[DB] Loaded for %s' % self.room_name)

    def load_modules(self):
        self.spamcheck = spam.Spam(self, pinylib.CONFIG)
        self.score = 0

        self.tokes = tokes.Tokes(self, pinylib.CONFIG)
        self.voting = voting.Voting(self, pinylib.CONFIG)

    def on_joined(self, client_info):
        """
        Received when the client have joined the room successfully.

        :param client_info: This contains info about the client, such as user role and so on.
        :type client_info: dict
        """
        log.info('client info: %s' % client_info)
        self.client_id = client_info['handle']
        self.is_client_mod = client_info['mod']
        self.is_client_owner = client_info['owner']
        client = self.users.add(client_info)
        client.user_level = 2
        self.console_write(pinylib.COLOR['white'],
                           '[Bot] connected as %s:%s, joining room %s' % (client.nick, client.id, self.room_name))

        threading.Thread(target=self.options).start()

        self.db_setup()
        self.load_modules()

        if not self.worker_kicks_working:
            self.worker_kicks()

        if not self.worker_bans_working:
            self.worker_bans()

    def on_join(self, join_info):
        """
        Received when a user joins the room.

        :param join_info: This contains user information such as role, account and so on.
        :type join_info: dict
        """
        time_join = time.time()

        log.info('user join info: %s' % join_info)
        _user = self.users.add(join_info)

        if _user.nick in self.buddy_db.nick_bans:
            if pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN:
                if self.spamcheck.lockdown:
                    self.process_kick(_user.id)
                else:
                    if pinylib.CONFIG.B_VERBOSE:
                        self.score = 10
                        self.handle_msg('\n %s %s kicked, banned nick.' % (self.boticon, _user.nick))
                    self.send_kick_msg(_user.id)
                    return
            else:
                if self.spamcheck.lockdown:
                    self.process_ban(_user.id)
                else:
                    self.send_ban_msg(_user.id)
                if pinylib.CONFIG.B_VERBOSE:
                    self.score = 10
                    self.handle_msg('\n %s %s banned, banned nick.' % (self.boticon, _user.nick))
                self.console_write(pinylib.COLOR['red'], '[Security] Banned: Nick %s' % _user.nick)
                return

        lockdowncheck = self.spamcheck.lockdown_onjoin(_user, time_join)

        if lockdowncheck:
            self.spamcheck.check_lockdown()
        else:
            self.usr_registration = register.Registration(self, self.spamcheck, pinylib.CONFIG)
            is_registered = self.usr_registration.user_register(_user)

            if is_registered and self.spamcheck.joind_count < 4:
                usr_welcome = welcome.Welcome(self, pinylib.CONFIG)
                usr_welcome.welcome(_user.id, self.usr_registration.greet)

    def on_nick(self, uid, nick):
        """
        Received when a user changes nick name.

        :param uid: The ID (handle) of the user.
        :type uid: int
        :param nick: The new nick name.
        :type nick: str
        """
        _user = self.users.search(uid)
        old_nick = _user.nick
        _user.nick = nick

        if _user.nick in self.buddy_db.nick_bans:
            if pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN:
                if self.spamcheck.lockdown:
                    self.process_kick(uid)
                else:
                    self.score = 10
                    self.send_kick_msg(uid)
            else:
                if self.spamcheck.lockdown:
                    self.process_ban(uid)
                else:
                    self.score = 10
                    self.send_ban_msg(uid)
            if pinylib.CONFIG.B_VERBOSE:
                self.handle_msg('\n %s %s changed nick to %s.' % (self.boticon, old_nick, _user.nick))

            self.console_write(pinylib.COLOR['bright_cyan'], '[User] %s:%s Changed nick to: %s' %
                               (old_nick, uid, nick))

    def do_op_user(self, user_name):
        """
        Lets the room owner, a mod or a bot controller make another user a bot controller.

        :param user_name: The user to op.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.handle_msg('Missing username.')
            else:
                _user = self.users.search_by_nick(user_name)
                if _user is not None:
                    _user.user_level = 4
                    self.handle_msg('No user named: %s' % user_name)

    def do_deop_user(self, user_name):
        """
        Lets the room owner, a mod or a bot controller remove a user from being a bot controller.

        :param user_name: The user to deop.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.handle_msg('Missing username.')
            else:
                _user = self.users.search_by_nick(user_name)

                if _user is not None:
                    if _user.account is not None:
                        _user.user_level = 6
                    else:
                        _user.user_level = 7
                        self.handle_msg('No user named: %s' % user_name)

    def do_clear(self):
        """ Clears the chat box. """
        self.send_chat_msg('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'
                           '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

    def do_user_info(self, user_name):
        """
        Shows user object info for a given user name.
        :param user_name: The user name of the user to show the info for.
        :type user_name: str
        """

        if self.is_client_mod:
            if len(user_name) is 0:
                self.handle_msg('Missing username.')
            else:
                _user = self.users.search_by_nick(user_name)
                if _user is None:
                    self.handle_msg('No user named: %s' % user_name)
                else:
                    if _user.account and _user.tinychat_id is None:
                        user_info = pinylib.apis.tinychat.user_info(_user.account)
                        if user_info is not None:
                            _user.tinychat_id = user_info['tinychat_id']
                            _user.last_login = user_info['last_active']
                    online_time = (pinylib.time.time() - _user.join_time)

                    info = [
                        'User Level: ' + str(_user.user_level),
                        'Online Time: ' + self.format_time(online_time),
                        'Last Message: ' + str(_user.last_msg)
                    ]
                    if _user.tinychat_id is not None:
                        info.append('Account: ' + str(_user.account))
                        info.append('Tinychat ID: ' + str(_user.tinychat_id))
                        info.append('Last Login: ' + _user.last_login)

                    self.handle_msg('\n'.join(info))

    # == Bot Police ==

    def do_kick(self, user_name):
        """
        Kick a user out of the room.

        :param user_name: The username to kick.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.handle_msg('Missing username.')
            elif user_name == self.nickname:
                self.message_handler('Action not allowed.')
            else:
                if user_name.startswith('*'):
                    user_name = user_name.replace('*', '')
                    _users = self.users.search_containing(user_name)
                    if len(_users) > 0:
                        for i, user in enumerate(_users):
                            if user.nick != self.nickname and user.user_level > self.active_user.user_level:
                                if i <= pinylib.CONFIG.B_MAX_MATCH_BANS - 1:
                                    self.send_kick_msg(user.id)
                else:
                    _user = self.users.search_by_nick(user_name)
                    if _user is None:
                        self.handle_msg('No user named: %s' % user_name)
                    elif _user.user_level < self.active_user.user_level:
                        self.handle_msg('imma let ya guys figure that out...')
                    else:
                        self.score = 10
                        self.send_kick_msg(_user.id)

    def do_ban(self, user_name):
        """
        Ban a user from the room.

        :param user_name: The username to ban.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.handle_msg('Missing username.')
            elif user_name == self.nickname:
                self.handle_msg('Action not allowed.')
            else:
                if user_name.startswith('*'):
                    user_name = user_name.replace('*', '')
                    _users = self.users.search_containing(user_name)
                    if len(_users) > 0:
                        for i, user in enumerate(_users):
                            if user.nick != self.nickname and user.user_level > self.active_user.user_level:
                                if i <= pinylib.CONFIG.B_MAX_MATCH_BANS - 1:
                                    self.send_ban_msg(user.id)
                else:
                    _user = self.users.search_by_nick(user_name)
                    if _user is None:
                        self.handle_msg('No user named: %s' % user_name)
                    elif _user.user_level < self.active_user.user_level:
                        self.handle_msg('i dont wanna be a part of ya problems..')
                    else:
                        self.score = 10
                        self.send_ban_msg(_user.id)

    def do_banlist_search(self, user_name):
        """
        Search the banlist for matches.
        NOTE: This method/command was meant to be a private message command,
        but it seems like the private messages is broken, so for now
        it will be a room command.
        :param user_name: The user name or partial username to search for.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) == 0:
                self.handle_msg('Missing user name to search for.')
            else:
                self.bl_search_list = self.users.search_banlist_containing(user_name)
                if len(self.bl_search_list) == 0:
                    self.handle_msg('No banlist matches.')
                else:
                    _ban_list_info = '\n'.join('(%s) %s:%s [%s]' % (i, user.nick, user.account, user.ban_id)
                                               for i, user in enumerate(self.bl_search_list))
                    self.handle_msg(_ban_list_info)

    def do_forgive(self, user_index):
        """
        Forgive a user from the ban list search.
        NOTE: This method/command was meant to be a private message command,
        but it seems like the private messages is broken, so for now
        it will be a room command.
        :param user_index: The index in the ban list search.
        :type user_index: str | int
        """
        if self.is_client_mod:
            try:
                user_index = int(user_index)
            except ValueError:
                self.handle_msg('Only numbers allowed (%s)' % user_index)
            else:
                if len(self.bl_search_list) > 0:
                    if user_index <= len(self.bl_search_list) - 1:
                        self.send_unban_msg(self.bl_search_list[user_index].ban_id)
                    else:
                        if len(self.bl_search_list) > 1:
                            self.handle_msg('Please make a choice between 0-%s' % len(self.bl_search_list))
                else:
                    self.handle_msg('The ban search is empty.')

    def do_unban(self, user_name):
        """
        Un-ban the last banned user or a user by user name.
        NOTE: experimental. In case the user name match more than one
        user in the banlist, then the last banned user will be unbanned.
        :param user_name: The exact user name to unban.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name.strip()) == 0:
                self.handle_msg('Missing user name.')
            elif user_name == '/':  # shortcut to the last banned user.
                last_banned_user = self.users.last_banned
                if last_banned_user is not None:
                    self.send_unban_msg(last_banned_user.ban_id)
                else:
                    self.handle_msg('Failed to find the last banned user.')
            else:
                banned_user = self.users.search_banlist_by_nick(user_name)
                if banned_user is not None:
                    self.send_unban_msg(banned_user.ban_id)
                else:
                    self.handle_msg('No user named: %s in the banlist.' % user_name)

    # == Tinychat Broadcasting ==

    def on_publish(self, uid):
        _user = self.users.search(uid)

        if pinylib.CONFIG.B_ALLOW_BROADCASTS:
            if _user is not None:
                if _user.user_level == 8 or _user.nick in self.cambans:
                    self.score = 10
                    self.send_close_user_msg(_user.id)
                    self.handle_msg('%s is banned from camming up.' % _user.nick)
                    _user.is_broadcasting = False
                    self.send_kick_msg(_user.id)
            _user.is_broadcasting = True

        else:
            self.send_close_user_msg(_user.id)
            self.handle_msg('Broadcating is disabled, allowcam to enable.')
            _user.is_broadcasting = False

    def do_cam_approve(self, user_name):
        """
        Allow a user to broadcast in a green room enabled room.

        :param user_name:  The name of the user allowed to broadcast.
        :type user_name: str
        """
        if pinylib.CONFIG.B_ALLOW_BROADCASTS:

            _user = self.users.search_by_nick(user_name)

            if _user is None:
                return

            if len(user_name) > 0:
                if _user.user_level == 8 or _user.nick in self.cambans:
                    self.handle_msg('%s is banned from camming here.' % _user.nick)
                    return

                if _user.is_waiting:
                    self.send_cam_approve_msg(_user.id)
            else:
                self.handle_msg('No user named: %s' % user_name)
        else:
            self.handle_msg('Broadcasting is disabled.')

    def do_close_broadcast(self, user_name):
        """
        Close a users broadcast.

        :param user_name: The name of the user to close.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) == 0:
                self.handle_msg('Mising user name.')
            else:
                _user = self.users.search_by_nick(user_name)
                broadcasters = self.users.broadcaster

                if _user in broadcasters:

                    if _user.user_level < self.active_user.user_level:
                        self.send_close_user_msg(_user.id)
                        _user.is_broadcasting = False
                else:
                    self.handle_msg('%s is not broadcasting.' % user_name)

    def on_pending_moderation(self, pending):
        _user = self.users.search(pending['handle'])
        if _user is not None:

            if _user.user_level == 8 or _user.nick in self.cambans:
                self.handle_msg('%s is banned from camming up.' % _user.nick)
                self.score = 10
                self.send_kick_msg(_user.id)
                return

            if _user.user_level < 5:
                self.send_cam_approve_msg(_user.id)
                _user.is_broadcasting = True
            else:
                _user.is_waiting = True
                self.send_chat_msg('%s is waiting in the greenroom.' % _user.nick)

    # == Bot Cmd Handler ==

    def cmd_handler(self, msg):

        prefix = pinylib.CONFIG.B_PREFIX

        parts = msg.split(' ')
        cmd = parts[0].lower().strip()
        cmd_arg = ' '.join(parts[1:]).strip()

        _user = self.users.search_by_nick(self.active_user.nick)

        # == Moderator level ==

        if _user.user_level < 4:

            if cmd == prefix + '+chatmod':
                self.buddy_db.add_user(cmd_arg, 4)
                _user.user_level = 4
                self.handle_msg('%s was added to Chat Mods.' % cmd_arg)

            elif cmd == prefix + '-chatmod':
                self.buddy_db.remove_user(cmd_arg)
                self.handle_msg('%s was removed from Chat Mods.' % cmd_arg)

            elif cmd == prefix + 'spam':
                self.do_spam_protection()

            elif cmd == prefix + 'vip':
                self.do_vip()
            elif cmd == prefix + 'allowcam':
                self.do_allowcams()

            elif cmd == prefix + 'noguest':
                self.do_guests(0)

            elif cmd == prefix + 'verbose':
                self.do_verbose(0)

            elif cmd == prefix + 'greet':
                self.do_greet(0)

            elif cmd == prefix + 'lurkers':
                self.do_lurkers()

            elif cmd == prefix == 'kb':
                self.do_kick_as_ban(0)

            if cmd == prefix + 'lockdown':
                self.spamcheck.do_lockdown(1)
                self.spamcheck.check_lockdown()

            if self.is_client_owner:
                if cmd == prefix + 'lockup':
                    self.spamcheck.do_lockdown(0)
                    self.spamcheck.check_lockdown()

            if cmd == prefix + 'announcement':
                self.do_announcement(cmd_arg)

        # == Administrator/Owner Level ==

        if _user.user_level == 2:
            if self.is_client_owner:

                if cmd == prefix + 'p2t':
                    threading.Thread(target=self.do_push2talk).start()
                elif cmd == prefix + 'dir':
                    threading.Thread(target=self.do_directory).start()
                elif cmd == prefix + '+mod':
                    threading.Thread(target=self.do_make_mod, args=(cmd_arg,)).start()
                elif cmd == prefix + '-mod':
                    threading.Thread(target=self.do_remove_mod, args=(cmd_arg,)).start()

        # == Moderator level users ==

        if _user.user_level < 5:

            if cmd == prefix + '+tmod':
                self.do_op_user(cmd_arg)

            elif cmd == prefix + '-tmod':
                self.do_deop_user(cmd_arg)

            elif cmd == prefix + 'who':
                self.do_user_info(cmd_arg)

            elif cmd == prefix + 'clr':
                self.do_clear()

            elif cmd == prefix + 'sbl':
                self.do_banlist_search(cmd_arg)

            elif cmd == prefix + 'fg':
                self.do_forgive(cmd_arg)

            elif cmd == prefix + 'unb':
                self.do_unban(cmd_arg)

            elif cmd == prefix + 'kick':
                threading.Thread(target=self.do_kick,
                                 args=(cmd_arg,)).start()

            elif cmd == prefix + 'ban':
                threading.Thread(target=self.do_ban,
                                 args=(cmd_arg,)).start()

            elif cmd == prefix + 'cam':
                self.do_cam_approve(cmd_arg)

            elif cmd == prefix + 'close':
                self.do_close_broadcast(cmd_arg)

            elif cmd == prefix + '+badnick':
                self.buddy_db.add_bad_nick(cmd_arg)
                self.handle_msg('%s was added to bad nicks' % cmd_arg)

            elif cmd == prefix + '-badnick':
                self.buddy_db.remove_bad_nick(cmd_arg)
                self.handle_msg('%s was removed from bad nicks.' % cmd_arg)

            elif cmd == prefix + '+banword':
                self.buddy_db.add_bad_word(cmd_arg)
                self.handle_msg('%s was added to banned words.' % cmd_arg)

            elif cmd == prefix + '-banword':
                self.buddy_db.remove_bad_word(cmd_arg)
                self.handle_msg('%s was removed from banned words.' % cmd_arg)

            if cmd == prefix + 'dj':
                threading.Thread(target=self.do_dj,
                                 args=(cmd_arg,)).start()
            elif cmd == prefix + 'djmode':
                self.do_dj_mode()

        # == Known accounts only ==

        if _user.user_level < 6:
            canplay = 1

            if self.dj_mode:
                canplay = 0

                if _user.account in self.djs:
                    canplay = 1

            if cmd == prefix + 'skip':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_skip()

            elif cmd == prefix + 'media':
                self.do_media_info()

            elif cmd == prefix + 'yt':
                if not canplay:
                    self.do_djmsg()
                else:
                    threading.Thread(
                        target=self.do_play_youtube, args=(cmd_arg,)).start()

            elif cmd == prefix + 'yts':
                if not canplay:
                    self.do_djmsg()
                else:
                    threading.Thread(
                        target=self.do_youtube_search, args=(cmd_arg,)).start()

            elif cmd == prefix + 'del':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_delete_playlist_item(cmd_arg)

            elif cmd == prefix + 'replay':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_media_replay()

            elif cmd == prefix + 'play':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_play_media()

            elif cmd == prefix + 'pause':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_media_pause()

            elif cmd == prefix + 'seek':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_seek_media(cmd_arg)

            elif cmd == prefix + 'stop':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_close_media()

            elif cmd == prefix + 'reset':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_clear_playlist()

            elif cmd == prefix + 'next':
                if not canplay:
                    self.do_djmsg()
                else:
                    self.do_next_tune_in_playlist()

            elif cmd == prefix + 'playlist':
                self.do_playlist_info()

            elif cmd == prefix + 'pyts':
                self.do_play_youtube_search(cmd_arg)

            elif cmd == prefix + 'pls':
                threading.Thread(
                    target=self.do_youtube_playlist_search, args=(cmd_arg,)).start()

            elif cmd == prefix + 'plp':
                threading.Thread(
                    target=self.do_play_youtube_playlist, args=(cmd_arg,)).start()

            elif cmd == prefix + 'ssl':
                self.do_show_search_list()

            elif cmd == prefix + 'whatsong':
                self.do_now_playing()

            if cmd == prefix + 'status':
                self.do_playlist_status()

            elif cmd == prefix + 'now':
                self.do_now_playing()

            elif cmd == prefix + 'whoplayed':
                self.do_who_plays()

        # == Any user can access ==
        # == Tinychat API Cmds ==
        if cmd == prefix + 'acspy':
            threading.Thread(target=self.do_account_spy, args=(cmd_arg,)).start()

        elif cmd == prefix + 'help':
            self.do_help()

        # == Other Cmds ==
        if cmd == prefix + 'urb':
            threading.Thread(target=self.do_search_urban_dictionary, args=(cmd_arg,)).start()

        elif cmd == prefix + 'wea':
            threading.Thread(target=self.do_weather_search, args=(cmd_arg,)).start()

        elif cmd == prefix + 'ip':
            threading.Thread(target=self.do_whois_ip, args=(cmd_arg,)).start()

        # == Fun APIs ==
        elif cmd == prefix + 'cn':
            threading.Thread(target=self.do_chuck_noris).start()

        elif cmd == prefix + '8ball':
            self.do_8ball(cmd_arg)

        elif cmd == prefix + 'roll':
            self.do_dice()

        elif cmd == prefix + 'flip':
            self.do_flip_coin()

        # == Toke Thing / Voteban==

        if cmd == prefix + 'tokes':
            self.tokes.tokesession(cmd_arg)

        if cmd == prefix + 'cheers':
            self.tokes.tokesession(cmd_arg)

        if cmd == prefix + 'vote':
            self.voting.votesession(cmd_arg)

        # == User Management ==

        if cmd == prefix + 'acc':  # !acc add <account> level note/msg  or !acc del <account>
            self.accountmanager(cmd_arg)

        if cmd == prefix + 'camban':  # dirty 2 minutes hack code /// requested guest camban
            _user = self.users.search_by_nick(cmd_arg)
            if _user is not None:
                if cmd_arg in self.cambans:
                    self.cambans.remove(cmd_arg)
                    _user.user_level = 7
                    self.handle_msg('%s is allowed to broadcast again.' % cmd_arg)
                    return
                else:
                    _user.user_level = 8
                    self.cambans.append(cmd_arg)
                    if _user.is_broadcasting:
                        self.send_close_user_msg(_user.id)
                        _user.is_broadcasting = False
            else:
                self.handle_msg('no such user')
            self.handle_msg('%s is now banned from camming' % cmd_arg)

        self.console_write(pinylib.COLOR['green'], self.active_user.nick + ': ' + cmd + ' ' + cmd_arg)

    def message_handler(self, msg):
        """
        A basic handler for chat messages.

        Overrides message_handler in pinylib
        to allow commands.

        :param msg: The chat message.
        :type msg: str
        """
        prefix = pinylib.CONFIG.B_PREFIX

        if msg.startswith(prefix):
            self.cmd_handler(msg)
        else:
            self.score = self.spamcheck.check_msg(msg)
            self.console_write(pinylib.COLOR['white'],
                               '(' + str(self.score) + ') ' + self.active_user.nick + ': ' + msg)
            self.active_user.last_msg = msg

    def private_message_handler(self, private_msg):
        """
        Private message handler.

        Overrides private_message_handler in pinylib
        to enable private commands.

        :param private_msg: The private message.
        :type private_msg: str
        """
        prefix = pinylib.CONFIG.B_PREFIX

        if private_msg.startswith(prefix):
            self.cmd_handler(private_msg)

        self.console_write(pinylib.COLOR['white'], '[PRIMSG] %s: %s' % (self.active_user.nick, private_msg))

    # Youtube (Nortxort)

    def do_play_youtube(self, search_str):
        """
        Plays a youtube video matching the search term.

        :param search_str: The search term.
        :type search_str: str
        """
        log.info('user: %s:%s is searching youtube: %s' %
                 (self.active_user.nick, self.active_user.id, search_str))
        if self.is_client_mod:
            if len(search_str) is 0:
                self.send_chat_msg('Please specify youtube title, id or link.')
            else:
                _youtube = youtube.search(search_str)
                if _youtube is None:
                    log.warning('youtube request returned: %s' % _youtube)
                    self.send_chat_msg('Could not find video: ' + search_str)
                else:
                    log.info('youtube found: %s' % _youtube)
                    if self.playlist.has_active_track:
                        track = self.playlist.add(
                            self.active_user.nick, _youtube)
                        self.send_chat_msg('(%s) %s %s' %
                                           (self.playlist.last_index, track.title, self.format_time(track.time)))
                    else:
                        track = self.playlist.start(
                            self.active_user.nick, _youtube)
                        self.send_yut_play(track.id, track.time, track.title)
                        self.timer(track.time)

    def do_playlist_status(self):
        """ Shows the playlist queue. """
        if self.is_client_mod:
            if len(self.playlist.track_list) == 0:
                self.send_chat_msg('The playlist is empty.')
            else:
                queue = self.playlist.queue
                if queue is not None:
                    self.send_chat_msg('%s items in the playlist, %s still in queue.' %
                                       (queue[0], queue[1]))

    def do_next_tune_in_playlist(self):
        """ Shows the next track in the playlist. """
        if self.is_client_mod:
            if self.playlist.is_last_track is None:
                self.send_chat_msg('The playlist is empty.')
            elif self.playlist.is_last_track:
                self.send_chat_msg('This is the last track.')
            else:
                pos, next_track = self.playlist.next_track_info()
                if next_track is not None:
                    self.send_chat_msg('(%s) %s %s' %
                                       (pos, next_track.title, self.format_time(next_track.time)))

    def do_now_playing(self):
        """ Shows what track is currently playing. """
        if self.is_client_mod:
            if self.playlist.has_active_track:
                track = self.playlist.track
                if len(self.playlist.track_list) > 0:
                    self.handle_msg('(%s) %s %s' % (self.playlist.current_index, track.title,
                                                    self.format_time(track.time)))
                else:
                    self.handle_msg('%s %s' %
                                    (track.title, self.format_time(track.time)))
            else:
                self.handle_msg('No track playing.')

    def do_who_plays(self):
        """ Show who requested the currently playing track. """
        if self.is_client_mod:
            if self.playlist.has_active_track:
                track = self.playlist.track
                ago = self.format_time(
                    int(pinylib.time.time() - track.rq_time))
                self.send_chat_msg(
                    '%s requested this track %s ago.' % (track.owner, ago))
            else:
                self.send_chat_msg('No track playing.')

    def do_media_replay(self):
        """ Replay the currently playing track. """
        if self.is_client_mod:
            if self.playlist.track is not None:
                self.cancel_timer()
                track = self.playlist.replay()
                self.send_yut_play(track.id, track.time, track.title)
                self.timer(track.time)

    def do_play_media(self):
        """ Play a track on pause . """
        if self.is_client_mod:
            if self.playlist.track is not None:
                if self.playlist.has_active_track:
                    self.cancel_timer()
                if self.playlist.is_paused:
                    self.playlist.play(self.playlist.elapsed)
                    self.send_yut_play(self.playlist.track.id, self.playlist.track.time,
                                       self.playlist.track.title, self.playlist.elapsed)  #
                    self.timer(self.playlist.remaining)

    def do_media_pause(self):
        """ Pause a track. """
        if self.is_client_mod:
            track = self.playlist.track
            if track is not None:
                if self.playlist.has_active_track:
                    self.cancel_timer()
                self.playlist.pause()
                self.send_yut_pause(track.id, track.time,
                                    self.playlist.elapsed)

    def do_close_media(self):
        """ Close a track playing. """
        if self.is_client_mod:
            if self.playlist.has_active_track:
                self.cancel_timer()
                self.playlist.stop()
                self.send_yut_stop(
                    self.playlist.track.id, self.playlist.track.time, self.playlist.elapsed)

    def do_seek_media(self, time_point):
        """
        Time search a track.

        :param time_point: The time point in which to search to.
        :type time_point: str
        """
        if self.is_client_mod:
            if ('h' in time_point) or ('m' in time_point) or ('s' in time_point):
                offset = pinylib.string_util.convert_to_seconds(time_point)
                if offset == 0:
                    self.send_chat_msg('Invalid seek time.')
                else:
                    track = self.playlist.track
                    if track is not None:
                        if 0 < offset < track.time:
                            if self.playlist.has_active_track:
                                self.cancel_timer()
                            if self.playlist.is_paused:
                                self.playlist.pause(offset=offset)  #
                                self.send_yut_pause(
                                    track.id, track.time, offset)
                            else:
                                self.playlist.play(offset)
                                self.send_yut_play(
                                    track.id, track.time, track.title, offset)
                                self.timer(self.playlist.remaining)

    def do_clear_playlist(self):
        """ Clear the playlist for items."""
        if self.is_client_mod:
            if len(self.playlist.track_list) > 0:
                pl_length = str(len(self.playlist.track_list))
                self.playlist.clear()
                self.send_chat_msg(
                    'Deleted %s items in the playlist.' % pl_length)
            else:
                self.send_chat_msg('The playlist is empty, nothing to delete.')

    def do_playlist_info(self):  # TODO: this needs more work !
        """ Shows the next tracks in the playlist. """
        if self.is_client_mod:
            if len(self.playlist.track_list) > 0:
                tracks = self.playlist.get_tracks()
                if len(tracks) > 0:
                    # If i is 0 then mark that as the next track
                    _ = '\n'.join('(%s) - %s %s' % (track[0], track[1].title, self.format_time(track[1].time))
                                  for i, track in enumerate(tracks))
                    self.send_chat_msg(_)

    def do_youtube_search(self, search_str):
        """
        Search youtube for a list of matching candidates.

        :param search_str: The search term to search for.
        :type search_str: str
        """
        if self.is_client_mod:
            if len(search_str) == 0:
                self.send_chat_msg('Missing search string.')
            else:
                self.search_list = youtube.search_list(search_str, results=5)
                if len(self.search_list) > 0:
                    self.is_search_list_yt_playlist = False
                    _ = '\n'.join('(%s) %s %s' % (i, d['video_title'], self.format_time(d['video_time']))
                                  for i, d in enumerate(self.search_list))  #
                    self.send_chat_msg(_)
                else:
                    self.send_chat_msg(
                        'Could not find anything matching: %s' % search_str)

    def do_play_youtube_search(self, int_choice):
        """
        Play a track from a previous youtube search list.

        :param int_choice: The index of the track in the search.
        :type int_choice: str | int
        """
        if self.is_client_mod:
            if not self.is_search_list_yt_playlist:
                if len(self.search_list) > 0:
                    try:
                        int_choice = int(int_choice)
                    except ValueError:
                        self.send_chat_msg('Only numbers allowed.')
                    else:
                        if 0 <= int_choice <= len(self.search_list) - 1:

                            if self.playlist.has_active_track:
                                track = self.playlist.add(
                                    self.active_user.nick, self.search_list[int_choice])
                                self.send_chat_msg('Added (%s) %s %s' %
                                                   (self.playlist.last_index,
                                                    track.title, self.format_time(track.time)))
                            else:
                                track = self.playlist.start(
                                    self.active_user.nick, self.search_list[int_choice])
                                self.send_yut_play(
                                    track.id, track.time, track.title)
                                self.timer(track.time)
                        else:
                            self.send_chat_msg(
                                'Please make a choice between 0-%s' % str(len(self.search_list) - 1))
                else:
                    self.send_chat_msg(
                        'No youtube track id\'s in the search list.')
            else:
                self.send_chat_msg(
                    'The search list only contains youtube playlist id\'s.')

    def on_yut_play(self, yt_data):
        """
        Received when a youtube gets started or time searched.

        This also gets received when the client starts a youtube, the information is
        however ignored in that case.

        :param yt_data: The event information contains info such as the ID (handle) of the user
        starting/searching the youtube, the youtube ID, youtube time and so on.
        :type yt_data: dict
        """
        user_nick = 'n/a'
        if 'handle' in yt_data:
            if yt_data['handle'] != self.client_id:
                _user = self.users.search(yt_data['handle'])
                user_nick = _user.nick

        if self.playlist.has_active_track:
            self.cancel_timer()

        if yt_data['item']['offset'] == 0:
            _youtube = youtube.video_details(yt_data['item']['id'], False)
            self.playlist.start(user_nick, _youtube)
            self.timer(self.playlist.track.time)
            self.console_write(pinylib.COLOR['bright_magenta'], '[Media] %s started youtube video (%s)' %
                               (user_nick, yt_data['item']['id']))
        elif yt_data['item']['offset'] > 0:
            if user_nick == 'n/a':
                _youtube = youtube.video_details(yt_data['item']['id'], False)
                self.playlist.start(user_nick, _youtube)
                offset = self.playlist.play(yt_data['item']['offset'])
                self.timer(offset)
            else:
                offset = self.playlist.play(yt_data['item']['offset'])
                self.timer(offset)
                self.console_write(pinylib.COLOR['bright_magenta'], '[Media] %s searched the youtube video to: %s' %
                                   (user_nick, int(round(yt_data['item']['offset']))))

    def on_yut_pause(self, yt_data):
        """
        Received when a youtube gets paused or searched while paused.

        This also gets received when the client pauses or searches while paused, the information is
        however ignored in that case.

        :param yt_data: The event information contains info such as the ID (handle) of the user
        pausing/searching the youtube, the youtube ID, youtube time and so on.
        :type yt_data: dict
        """
        if 'handle' in yt_data:
            if yt_data['handle'] != self.client_id:
                _user = self.users.search(yt_data['handle'])
                if self.playlist.has_active_track:
                    self.cancel_timer()
                self.playlist.pause()
                self.console_write(pinylib.COLOR['bright_magenta'], '[Media] %s paused the video at %s' %
                                   (_user.nick, int(round(yt_data['item']['offset']))))

    def do_youtube_playlist_search(self, search_str):
        """
        Search youtube for a playlist.

        :param search_str: The search term to search for.
        :type search_str: str
        """
        if self.is_client_mod:
            if len(search_str) == 0:
                self.send_chat_msg('Missing search string.')
            else:
                self.search_list = youtube.playlist_search(search_str)
                if len(self.search_list) > 0:
                    self.is_search_list_yt_playlist = True
                    _ = '\n'.join('(%s) %s' % (
                        i, d['playlist_title']) for i, d in enumerate(self.search_list))
                    self.send_chat_msg(_)
                else:
                    self.send_chat_msg(
                        'Failed to find playlist matching search term: %s' % search_str)

    def do_play_youtube_playlist(self, int_choice):
        """
        Play a previous searched playlist.

        :param int_choice: The index of the playlist.
        :type int_choice: str | int
        """
        if self.is_client_mod:
            if self.is_search_list_yt_playlist:
                try:
                    int_choice = int(int_choice)
                except ValueError:
                    self.send_chat_msg('Only numbers allowed.')
                else:
                    if 0 <= int_choice <= len(self.search_list) - 1:
                        self.send_chat_msg(
                            'Please wait while creating playlist..')
                        tracks = youtube.playlist_videos(
                            self.search_list[int_choice])
                        if len(tracks) > 0:
                            self.playlist.add_list(
                                self.active_user.nick, tracks)
                            self.send_chat_msg(
                                '🎶 Added %s tracks from youtube playlist.' % len(tracks))
                            if not self.playlist.has_active_track:
                                track = self.playlist.next_track
                                self.send_yut_play(
                                    track.id, track.time, track.title)
                                self.timer(track.time)
                        else:
                            self.send_chat_msg(
                                'Failed to retrieve videos from youtube playlist.')
                    else:
                        self.send_chat_msg(
                            'Please make a choice between 0-%s' % str(len(self.search_list) - 1))
            else:
                self.send_chat_msg(
                    'The search list does not contain any youtube playlist id\'s.')

    def do_show_search_list(self):
        """ Show what the search list contains. """
        if self.is_client_mod:
            if len(self.search_list) == 0:
                self.send_chat_msg('The search list is empty.')
            elif self.is_search_list_yt_playlist:
                _ = '\n'.join('(%s) - %s' % (i, d['playlist_title'])
                              for i, d in enumerate(self.search_list))
                self.send_chat_msg('Youtube Playlist\'s\n' + _)
            else:
                _ = '\n'.join('(%s) %s %s' % (i, d['video_title'], self.format_time(d['video_time']))
                              for i, d in enumerate(self.search_list))
                self.send_chat_msg('🎶 Youtube Tracks\n' + _)

    def do_skip(self):
        """ Skip to the next item in the playlist. """
        if self.is_client_mod:
            if self.playlist.is_last_track is None:
                self.send_chat_msg('No tunes to skip. The playlist is empty.')
            elif self.playlist.is_last_track:
                self.send_chat_msg('This is the last track in the playlist.')
            else:
                self.cancel_timer()
                next_track = self.playlist.next_track
                self.send_yut_play(
                    next_track.id, next_track.time, next_track.title)
                self.timer(next_track.time)

    # TODO: Make sure this is working.
    def do_delete_playlist_item(self, to_delete):
        """
        Delete items from the playlist.

        :param to_delete: Item indexes to delete.
        :type to_delete: str
        """
        if self.is_client_mod:
            if len(self.playlist.track_list) == 0:
                self.send_chat_msg('The playlist is empty.')
            elif len(to_delete) == 0:
                self.send_chat_msg('No indexes provided.')
            else:
                indexes = None
                by_range = False

                try:
                    if ':' in to_delete:
                        range_indexes = map(int, to_delete.split(':'))
                        temp_indexes = range(
                            range_indexes[0], range_indexes[1] + 1)
                        if len(temp_indexes) > 1:
                            by_range = True
                    else:
                        temp_indexes = map(int, to_delete.split(','))
                except ValueError as ve:
                    log.error('wrong format: %s' % ve)
                else:
                    indexes = []
                    for i in temp_indexes:
                        if i < len(self.playlist.track_list) and i not in indexes:
                            indexes.append(i)

                if indexes is not None and len(indexes) > 0:
                    result = self.playlist.delete(indexes, by_range)
                    if result is not None:
                        if by_range:
                            self.send_chat_msg('Deleted from index: %s to index: %s' %
                                               (result['from'], result['to']))
                        elif result['deleted_indexes_len'] is 1:
                            self.send_chat_msg('Deleted %s' %
                                               result['track_title'])
                        else:
                            self.send_chat_msg('Deleted tracks at index: %s' %
                                               ', '.join(result['deleted_indexes']))
                    else:

                        self.send_chat_msg('Nothing was deleted.')

    def do_media_info(self):
        """ Show information about the currently playing youtube. """
        if self.is_client_mod and self.playlist.has_active_track:
            self.send_chat_msg(
                'Playlist Tracks: ' + str(len(self.playlist.track_list)) + '\n' +
                'Track Title: ' + self.playlist.track.title + '\n' +
                'Track Index: ' + str(self.playlist.track_index) + '\n' +
                'Elapsed Track Time: ' + self.format_time(self.playlist.elapsed) + '\n' +
                'Remaining Track Time: ' +
                self.format_time(self.playlist.remaining)
            )

    # == Tinychat Owner / Utils ==

    def do_make_mod(self, account):
        """
        Make a tinychat account a room moderator.

        :param account: The account to make a moderator.
        :type account: str
        """
        if self.is_client_owner:
            if len(account) is 0:
                self.handle_msg('Missing account name.')
            else:
                tc_user = self.privacy_.make_moderator(account)
                if tc_user is None:
                    self.handle_msg('The account is invalid.')
                elif not tc_user:
                    self.handle_msg('%s is already a moderator.' % account)
                elif tc_user:
                    self.handle_msg('%s was made a room moderator.' % account)

    def do_remove_mod(self, account):
        """
        Removes a tinychat account from the moderator list.

        :param account: The account to remove from the moderator list.
        :type account: str
        """
        if self.is_client_owner:
            if len(account) is 0:
                self.handle_msg('Missing account name.')
            else:
                tc_user = self.privacy_.remove_moderator(account)
                if tc_user:
                    self.handle_msg('%s is no longer a room moderator.' % account)
                elif not tc_user:
                    self.handle_msg('%s is not a room moderator.' % account)

    def do_directory(self):
        """ Toggles if the room should be shown on the directory. """
        if self.is_client_owner:
            if self.privacy_.show_on_directory():
                self.handle_msg('Room IS shown on the directory.')
            else:
                self.handle_msg('Room is NOT shown on the directory.')

    def do_push2talk(self):
        """ Toggles if the room should be in push2talk mode. """
        if self.is_client_owner:
            if self.privacy_.set_push2talk():
                self.handle_msg('Push2Talk is enabled.')
            else:
                self.handle_msg('Push2Talk is disabled.')

    def do_green_room(self):
        """ Toggles if the room should be in greenroom mode. """
        if self.is_client_owner:
            if self.privacy_.set_greenroom():
                self.handle_msg('Green room is enabled.')
            else:
                self.handle_msg('Green room is disabled.')

    def do_clear_room_bans(self):
        """ Clear all room bans. """
        if self.is_client_owner:
            if self.privacy_.clear_bans():
                self.handle_msg('All room bans was cleared.')

    def do_kill(self):
        """ Kills the bot. """
        self.disconnect()

    def do_reboot(self):
        """ Reboots the bot. """
        self.reconnect()

    def options(self):
        """ Load/set special options. """

        log.info('options: is_client_owner: %s, is_client_mod: %s' %
                 (self.is_client_owner, self.is_client_mod))

        if self.is_client_owner:
            self.get_privacy_settings()

        if self.is_client_mod:
            self.send_banlist_msg()

    def get_privacy_settings(self):
        """ Parse the privacy settings page. """
        log.info('Parsing %s\'s privacy page.' % self.account)
        self.privacy_ = privacy.Privacy(proxy=None)
        self.privacy_.parse_privacy_settings()

    def do_guests(self, s):
        """ Toggles if guests are allowed to join the room or not. """
        pinylib.CONFIG.B_ALLOW_GUESTS = not pinylib.CONFIG.B_ALLOW_GUESTS

        if not s:
            self.handle_msg('Allow Guests: %s' % pinylib.CONFIG.B_ALLOW_GUESTS)

    def do_spam_protection(self):
        """ Toggles Spam Protection features """
        pinylib.CONFIG.B_SPAMP = not pinylib.CONFIG.B_SPAMP
        self.handle_msg('Spam Protection: %s' % pinylib.CONFIG.B_SPAMP)

    def do_vip(self):
        """ Toggles VIP Mode """
        pinylib.CONFIG.B_VIP = not pinylib.CONFIG.B_VIP
        self.handle_msg('VIPs only: %s' % pinylib.CONFIG.B_VIP)

    def do_allowcams(self):
        """ Toggles Cam Mode """
        pinylib.CONFIG.B_ALLOW_BROADCASTS = not pinylib.CONFIG.B_ALLOW_BROADCASTS
        self.handle_msg('Allow Cams: %s' % pinylib.CONFIG.B_ALLOW_BROADCASTS)

    def do_verbose(self, s):
        """ Toggles verbose Mode """
        pinylib.CONFIG.B_VERBOSE = not pinylib.CONFIG.B_VERBOSE
        if not s:
            self.handle_msg('Verbose: %s' % pinylib.CONFIG.B_VERBOSE)

    def do_lurkers(self):
        """ Toggles if lurkers are allowed or not. """
        pinylib.CONFIG.B_ALLOW_LURKERS = not pinylib.CONFIG.B_ALLOW_LURKERS
        self.handle_msg('Allow Lurkers: %s' % pinylib.CONFIG.B_ALLOW_LURKERS)

    def do_greet(self, s):
        """ Toggles if users should be greeted on entry. """
        pinylib.CONFIG.B_GREET = not pinylib.CONFIG.B_GREET
        if not s:
            self.handle_msg('Greet Users: %s' % pinylib.CONFIG.B_GREET)

    def do_kick_as_ban(self, s):
        """ Toggles if kick should be used instead of ban for auto bans . """
        pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN = not pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN
        if not s:
            self.handle_msg('Use Kick As Auto Ban: %s' % pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN)

    # == Python Timer Functions  ==

    def timer_event(self):
        """ This gets called when the timer has reached the time. """
        if len(self.playlist.track_list) > 0:
            if self.playlist.is_last_track:
                if self.is_connected:
                    self.send_chat_msg('Resetting playlist.')
                self.playlist.clear()
            else:
                track = self.playlist.next_track
                if track is not None and self.is_connected:
                    self.send_yut_play(track.id, track.time, track.title)
                self.timer(track.time)

    def timer(self, event_time):
        """
        Track event timer.

        This will cause an event to occur once the time is done.

        :param event_time: The time in seconds for when an event should occur.
        :type event_time: int | float
        """
        self.timer_thread = threading.Timer(event_time, self.timer_event)
        self.timer_thread.start()

    def cancel_timer(self):
        """ Cancel the track timer. """
        if self.timer_thread is not None:
            if self.timer_thread.is_alive():
                self.timer_thread.cancel()
                self.timer_thread = None
                return True
            return False
        return False

    @staticmethod
    def format_time(time_stamp, is_milli=False):
        """
        Converts a time stamp as seconds or milliseconds to (day(s)) hours minutes seconds.

        :param time_stamp: Seconds or milliseconds to convert.
        :param is_milli: The time stamp to format is in milliseconds.
        :return: A string in the format (days) hh:mm:ss
        :rtype: str
        """
        if is_milli:
            m, s = divmod(time_stamp / 1000, 60)
        else:
            m, s = divmod(time_stamp, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        if d == 0 and h == 0:
            human_time = '%02d:%02d' % (m, s)
        elif d == 0:
            human_time = '%d:%02d:%02d' % (h, m, s)
        else:
            human_time = '%d Day(s) %d:%02d:%02d' % (d, h, m, s)
        return human_time

    # == BuddyBot Additions ==
    # odsum.2018
    # DJ Mode
    # Kick/Ban Pooling
    # Room Announcement

    def handle_msg(self, msg):
        time.sleep(0.6)
        if pinylib.CONFIG.B_VERBOSE:
            self.send_chat_msg(msg)
        else:
            self.send_private_msg(self.active_user.id, msg)

    def worker_kicks(self):
        limit = 0
        self.worker_kicks_working = True
        while True:

            time.sleep(0.2)
            for k in self.kick_pool:
                if limit > 3:
                    time.sleep(2)
                    limit = 0
                else:
                    time.sleep(0.8)
                    self.kick_pool.remove(k)
                    self.send_kick_msg(k)
                    limit += 1
            if len(self.kick_pool) == 0:
                self.worker_kicks_working = False
                break

    def worker_bans(self):
        limit = 0
        self.worker_bans_working = True
        while True:
            time.sleep(0.2)
            for b in self.ban_pool:
                if limit > 3:
                    time.sleep(3)
                    limit = 0
                else:
                    time.sleep(0.8)
                    self.ban_pool.remove(b)
                    self.send_ban_msg(b)
                    limit += 1
            if len(self.ban_pool) == 0:
                self.worker_bans_working = False
                break

    def on_quit(self, uid):

        if pinylib.CONFIG.B_VERBOSE:
            if self.score < 2:
                _user = self.users.search(uid)
                msg = unicode("𝘭𝘦𝘧𝘵 𝘵𝘩𝘦 𝘳𝘰𝘰𝘮", 'utf-8')
                if _user is not None:
                    self.handle_msg('\n %s %s %s' % (self.boticon, _user.nick, msg))

        if uid in self.kick_pool:
            self.kick_pool.remove(uid)

        if uid in self.ban_pool:
            self.ban_pool.remove(uid)

    def process_kick(self, uid):
        if uid not in self.kick_pool:
            self.kick_pool.append(uid)
        if not self.worker_kicks_working:
            self.worker_kicks()

    def process_ban(self, uid):
        if uid not in self.ban_pool:
            self.ban_pool.append(uid)
        if not self.worker_bans_working:
            self.worker_bans()

    def do_djmsg(self):
        deejays = ",".join(self.djs)
        self.handle_msg('\n\n %s %s, %s is in DJ mode, current djs: %s' % (
            self.boticon, self.active_user.nick, self.room_name, deejays))

    def do_dj(self, account):
        _user = self.users.search_by_nick(account)

        if _user is None:
            self.handle_msg('\n\n %s %s has no account.' % (self.boticon, account))
        else:
            if _user.account in self.djs:
                self.djs.remove(_user.account)
                self.handle_msg('\n\n %s %s is not longer a dj.' % (self.boticon, _user.account))
            else:
                self.djs.append(_user.account)
                self.handle_msg('\n\n %s %s is now in the DJ crew.' % (self.boticon, _user.account))

    def do_dj_mode(self):
        if self.dj_mode == 0:
            self.dj_mode = 1
            self.handle_msg('\n\n %s Room is now in DJ mode!' % self.boticon)

        else:
            self.dj_mode = 0
            self.handle_msg(
                '\n\n %s DJ mode is off, you can add to the youtube playlist now.' % self.boticon)

    def do_announcement(self, announcement):
        self.tmp_announcement = announcement
        self.handle_msg('\n\n %s Room annoucement set to: %s' % (self.boticon, announcement))

    def announcement(self):
        announcement = pinylib.CONFIG.B_ANNOUNCEMENT
        if self.tmp_announcement is not None:
            announcement = self.tmp_announcement
        return announcement

    def do_help(self):
        """ Posts a link to github readme/wiki or other page about the bot commands. """

        ownr_cmds = ["reboot", "kb", "p2t", "dir"]
        admin_cmds = ["+mod", "-mod"]
        mod_cmds = ["announcement", "lockdown", "lockup", "+tmod", "-tmod", "spam", "vip", "verbose", "acc",
                    "allowcam"]
        cmod_cmds = ["clr", "camban", "kick", "ban", "unb", "sbl", "fg", "cam", "close", "+banwword", "-badword",
                     "noguest",
                     "greet", "lurkers", "vote ban/cam"]
        media_cmds = ["yt", "close", "seek", "reset", "spl", "del", "skip", "yts", "rpl", "pause", "play", "pyst"]
        public_cmds = ["urb", "wea", "ip", "cn", "8ball", "roll", "flip", "cheers", "tokes"]

        prefix = pinylib.CONFIG.B_PREFIX
        cmds_av = public_cmds

        if self.active_user.user_level < 3:
            cmds_av = cmds_av + admin_cmds
            if self.is_client_owner:
                cmds_av = cmds_av + ownr_cmds
        if self.active_user.user_level == 3:
            cmds_av = cmds_av + mod_cmds
        if self.active_user.user_level >= 3 and self.active_user.user_level > 5:
            cmds_av = cmds_av + cmod_cmds
        if self.active_user.user_level < 6:
            cmds_av = cmds_av + media_cmds

        cmds_av.sort()
        cmds_dump = [prefix + cmd for cmd in cmds_av]
        csets = zip(*[iter(cmds_dump)] * 8)
        self.send_private_msg(self.active_user.id, '\n\n %s Available Commands:' % self.boticon)

        for cset in csets:
            cmds = ", ".join(cset)
            time.sleep(1.5)
            self.send_private_msg(self.active_user.id, '%s' % cmds)

    def accountmanager(self, cmd_args):

        time.sleep(0.2)

        prefix = pinylib.CONFIG.B_PREFIX
        parts = cmd_args.split(' ')

        try:
            action = parts[0].lower().strip()
        except IndexError:
            self.handle_msg(
                'Action required: %sacc add [account] [mod/admin/verified/camban/ban] [welcomemsg/banreason] or %sacc del [account] [reason]' % (
                    prefix, prefix))
            return
        try:
            account = parts[1].lower().strip()
        except IndexError:
            self.handle_msg(
                'Account was missing: %sacc add [account] [mod/admin/verified/camban/ban] [welcomemsg/banreason] or %sacc del [account] [reason]' % (
                    prefix, prefix))
            return
        try:
            level = parts[2].lower().strip()
        except IndexError:
            level = 5  # default
        try:
            note = ' '.join(parts[3:]).strip()
        except IndexError:
            note = None  # default

        if level == "mod":
            level = 4
        if level == "admin":
            level = 2
        if level == "verified":
            level = 5
        if level == "whitelist":
            level = 5
        if level == "camban":
            level = 8
        if level == "ban":
            level = 9

        if self.active_user.user_level < level:
            if action == "del":
                self.buddy_db.remove_user(account)
                self.handle_msg('Account: %s was removed.' % account)

                _user = self.users.search_by_account(account)
                if _user is not None:
                    _user.user_level = 6
                return

        if self.active_user.user_level < 5:
            allowed = 0

            if action == "camban":
                message = self.active_user.account
                try:
                    note = ' '.join(parts[2:]).strip()
                except IndexError:
                    note = ''

                self.buddy_db.add_user(account, 8, note, message)
                self.handle_msg('Account: %s was added to cam bans.' % account)

                _user = self.users.search_by_account(account)
                if _user is not None:
                    _user.user_level = 8
                    if _user.is_broadcasting:
                        self.send_close_user_msg(_user.id)
                        _user.is_broadcasting = False

                return

            if action == "who":
                # user detailss,
                pass

            if action == "list":
                # list admin/mod/verified/all/banned
                pass

            if action == "ban":
                message = self.active_user.account
                try:
                    note = ' '.join(parts[2:]).strip()
                except IndexError:
                    note = ''
                self.buddy_db.add_user(account, 9, note, message)
                self.handle_msg('Account: %s was added to banned accounts.' % account)
                _user = self.users.search_by_account(account)
                if _user is not None:
                    self.send_ban_msg(_user.id)
                return

            if action == "add":
                message = ''

                if self.active_user.user_level < level:
                    allowed = 1

                if level < 6:
                    message = note
                    note = self.active_user.account

                if allowed:
                    self.buddy_db.add_user(account, level, note, message)
                    self.handle_msg('Account: %s was added!' % account)

                    _user = self.users.search_by_account(account)
                    if _user is not None:
                        _user.user_level = level
                else:
                    self.handle_msg('Account: insufficient privileges')
        return

    # == Tinychat API Command Methods. ==

    def do_account_spy(self, account):
        """
        Shows info about a tinychat account.
        :param account: tinychat account.
        :type account: str
        """
        if self.is_client_mod:
            if len(account) is 0:
                self.handle_msg('Missing username to search for.')
            else:
                tc_usr = pinylib.apis.tinychat.user_info(account)
                if tc_usr is None:
                    self.handle_msg('Could not find tinychat info for: %s' % account)
                else:
                    self.handle_msg('ID: %s, \nLast Login: %s' %
                                    (tc_usr['tinychat_id'], tc_usr['last_active']))

    # == Other API Command Methods. ==

    def do_search_urban_dictionary(self, search_str):
        """
        Shows urbandictionary definition of search string.
        :param search_str: The search string to look up a definition for.
        :type search_str: str
        """
        if self.is_client_mod:
            if len(search_str) is 0:
                self.send_chat_msg('Please specify something to look up.')
            else:
                urban = other.urbandictionary_search(search_str)
                if urban is None:
                    self.send_chat_msg('Could not find a definition for: %s' % search_str)
                else:
                    if len(urban) > 70:
                        chunks = pinylib.string_util.chunk_string(urban, 70)
                        for i in range(0, 2):
                            self.send_chat_msg(chunks[i])
                    else:
                        self.send_chat_msg(urban)

    def do_weather_search(self, search_str):
        """
        Shows weather info for a given search string.
        :param search_str: The search string to find weather data for.
        :type search_str: str
        """
        if len(search_str) is 0:
            self.send_chat_msg('Please specify a city to search for.')
        else:
            weather = other.weather_search(search_str)
            if weather is None:
                self.send_chat_msg('Could not find weather data for: %s' % search_str)
            else:
                self.send_chat_msg(weather)

    def do_whois_ip(self, ip_str):
        """
        Shows whois info for a given ip address or domain.
        :param ip_str: The ip address or domain to find info for.
        :type ip_str: str
        """
        if len(ip_str) is 0:
            self.send_chat_msg('Please provide an IP address or domain.')
        else:
            whois = other.whois(ip_str)
            if whois is None:
                self.send_chat_msg('No info found for: %s' % ip_str)
            else:
                self.send_chat_msg(whois)

    # == Just For Fun Command Methods. ==

    def do_chuck_noris(self):
        """ Shows a chuck norris joke/quote. """
        chuck = other.chuck_norris()
        if chuck is not None:
            self.send_chat_msg(chuck)

    def do_8ball(self, question):
        """
        Shows magic eight ball answer to a yes/no question.
        :param question: The yes/no question.
        :type question: str
        """
        if len(question) is 0:
            self.send_chat_msg('Question.')
        else:
            self.send_chat_msg('8Ball %s' % locals_.eight_ball())

    def do_dice(self):
        """ roll the dice. """
        self.send_chat_msg('The dice rolled: %s' % locals_.roll_dice())

    def do_flip_coin(self):
        """ Flip a coin. """
        self.send_chat_msg('The coin was: %s' % locals_.flip_coin())
