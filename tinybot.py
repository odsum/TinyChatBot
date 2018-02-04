# -*- coding: utf-8 -*-
""" Tinybot by Nortxort (https://github.com/nortxort/tinybot-rtc) """
""" Modified by odsum (https://github.com/odsum) """

import time
import logging
import threading
import os
import pinylib

from page import privacy
from util import tracklist
from apis import youtube, other, locals_

import random
from random import randint

import pickledb

__version__ = '2.0.3'

log = logging.getLogger(__name__)

joind_time = 0
joind_count = 0
bad_nick = 0
autoban_time = 0
autoban_count = 0
newnick = 0
ban_time = 0
spam = 0
spammer = 0
lastmsgs = []

dj_mode = 0
djs = []



# Random password words
_KEYWORDS = ["fob", "fobcity", "terima", "halal", "haram", "roses", ]


class TinychatBot(pinylib.TinychatRTCClient):
    privacy_ = None
    timer_thread = None
    playlist = tracklist.PlayList()
    search_list = []
    is_search_list_yt_playlist = False

    @property
    def config_path(self):
        """ Returns the path to the rooms configuration directory. """
        return pinylib.CONFIG.CONFIG_PATH + self.room_name + '/'

    global lockdown
    global userdb
    global db

    lockdown = False

    userdb = pinylib.CONFIG.CONFIG_PATH + pinylib.CONFIG.ROOM + '/' + 'user.db'
    db = pickledb.load(userdb, False)

    def isWord(self, word):

        VOWELS = "aeiou"
        PHONES = ['sh', 'ch', 'ph', 'sz', 'cz', 'sch', 'rz', 'dz']
        prevVowel = False

        if word:
            consecutiveVowels = 0
            consecutiveConsonents = 0
            for idx, letter in enumerate(word.lower()):
                vowel = True if letter in VOWELS else False

                if idx:
                    prev = word[idx - 1]
                    if prev in VOWELS:
                        prevVowel = True
                    if not vowel and letter == 'y' and not prevVowel:
                        vowel = True

                if prevVowel != vowel:
                    consecutiveVowels = 0
                    consecutiveConsonents = 0

                if vowel:
                    consecutiveVowels += 1
                else:
                    consecutiveConsonents += 1

                if consecutiveVowels >= 3 or consecutiveConsonents > 3:
                    return False

                if consecutiveConsonents == 3:
                    subStr = word[idx - 2:idx + 1]
                    if any(phone in subStr for phone in PHONES):
                        consecutiveConsonents -= 1
                        continue
                    return False

        return True

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
        client.user_level = 3
        self.console_write(pinylib.COLOR[
                           'bright_green'], '[User] Client joined the room: %s:%s' % (client.nick, client.id))

        threading.Thread(target=self.options).start()

        if not os.path.exists(userdb):
           
            db.dcreate('users')
            db.dcreate('badwords')
            db.dcreate('badnicks')
            db.dump()
            
            self.console_write(pinylib.COLOR['bright_green'], '[DB] Created')
        
        else:
            db = pickledb.load(userdb, False)
            self.console_write(pinylib.COLOR['bright_green'], '[DB] Loaded')

    def on_join(self, join_info):
        """
        Received when a user joins the room.

        :param join_info: This contains user information such as role, account and so on.
        :type join_info: dict
        """

        global joind_time
        global joind_count
        global autoban_time
        global lockdown
        global bad_nick

        time_join = time.time()

        log.info('user join info: %s' % join_info)
        _user = self.users.add(join_info)

        if self.nick_check(_user.nick):
            if pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN:
                self.send_kick_msg(_user.id)
            else:
                self.send_ban_msg(_user.id)
                self.console_write(pinylib.COLOR['cyan'], '[Security] Banned: Nick %s' % (_user.nick))

        if _user.account:
            if _user.is_owner:
                _user.user_level = 1
                self.console_write(pinylib.COLOR['red'], '[User] Room Owner %s:%d:%s' %
                                   (_user.nick, _user.id, _user.account))
            elif _user.is_mod:

                _user.user_level = 3
                self.console_write(pinylib.COLOR['bright_red'], '[User] Moderator %s:%d:%s' %
                                   (_user.nick, _user.id, _user.account))

            else:
                if db.dexists('users', _user.account):
                    _user.user_level = self.user_check(_user.account)
                    self.console_write(pinylib.COLOR['bright_red'], '[User] Found, level(%s)  %s:%d:%s' % (
                        _user.user_level, _user.nick, _user.id, _user.account))

                else:
                    _user.user_level = 6
                    self.console_write(pinylib.COLOR['bright_red'], '[User] Not verified %s:%d:%s' % (
                        _user.nick, _user.id, _user.account))

                if self.user_check(_user.account) == 9 and self.is_client_mod:
                    if pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN:
                        self.send_kick_msg(_user.id)
                    else:
                        self.send_ban_msg(_user.id)
                    self.console_write(
                        pinylib.COLOR['cyan'], '[Security] Banned: Account %s' % (_user.account))

                else:

                    tc_info = pinylib.apis.tinychat.user_info(_user.account)
                    if tc_info is not None:
                        _user.tinychat_id = tc_info['tinychat_id']
                        _user.last_login = tc_info['last_active']

        else:
            _user.user_level = 7
            self.console_write(
                pinylib.COLOR['bright_red'], '[User] Guest %s:%d' % (_user.nick, _user.id))

        if lockdown and autoban_time != 0:
            if time_join - 240 > autoban_time:
                if lockdown == 1:
                    soft = 1
                    self.do_lockdown(soft)
                    autoban_time = 0
                    bad_nick = 0
                    self.console_write(
                        pinylib.COLOR['cyan'], '[Security] Lockdown Mode Reset')
        else:

            maxtime = 7
            maxjoins = 8

            if joind_time == 0:
                joind_time = time.time()
                joind_count += 1

            elif time_join - joind_time > maxtime:
                joind_count = 0
                joind_time = 0
                bad_nick = 0

            elif joind_count > maxjoins:

                soft = 0
                self.do_lockdown(soft)
                autoban_time = time_join
                self.console_write(
                    pinylib.COLOR['cyan'], '[Security] Lockdown started')
            else:
                joind_count += 1

            if not self.isWord(_user.nick):
                bad_nick += 1

            if bad_nick > 3:
                time.sleep(1.0)
                # if self.user_check(_user.account) == 6 and self.is_client_mod:
                #   self.do_bad_account(_user.account)
                # spam accounts will make database file too big, maybe a
                # different db file is needed
                self.send_ban_msg(_user.id)
                self.console_write(pinylib.COLOR[
                                   'cyan'], '[Security] Randomized Nick Banned: Nicks %s' % (_user.nick))

        if not pinylib.CONFIG.B_ALLOW_GUESTS:
            if _user.user_level == 7:
                self.send_ban_msg(_user.id)
                self.console_write(pinylib.COLOR[
                                   'cyan'], '[Security] %s was banned on no guest mode' % (_user.nick))

        self.console_write(pinylib.COLOR['cyan'], '[User] %s:%d joined the room. (%s)' % (
            _user.nick, _user.id, joind_count))
        threading.Thread(target=self.welcome, args=(_user.id,)).start()

    def welcome(self, uid):
        time.sleep(5)
        _user = self.users.search(uid)

        if _user is not None:
            if pinylib.CONFIG.B_ALLOW_GUESTS:
                if pinylib.CONFIG.B_GREET and _user is not None:
                    if not _user.nick.startswith('guest-'):
                        if _user.user_level < 4:
                            pass
                            #self.send_private_msg(_user.id, 'You have Mod access - !help')
                        elif _user.user_level == 5:
                            pass
                            #self.send_private_msg(_user.id, 'You are verified, you add to the Youtube social playlist via !yt - Other cmds type !help')
                        elif _user.user_level == 6:
                            #self.send_private_msg(_user.id, 'Welcome to %s - ask to have your account verified.' % (self.room_name))
                            self.send_chat_msg(
                                'Welcome to %s %s - ask to have your account verified.' % (self.room_name, _user.nick))
                        elif _user.user_level == 7:
                            #self.send_private_msg(_user.id, 'Welcome to %s - we suggest making an account, personal info trolling or sexual harassment will not be tolerated.' % (self.room_name))
                            self.send_chat_msg('Welcome to %s %s, we suggest making an account.' % (
                                self.room_name, _user.nick))

    def on_pending_moderation(self, pending):
        _user = self.users.search(pending['handle'])
        if _user is not None:
            if self.user_check(_user.account) == 5 or self.user_check(_user.account) == 4:
                self.send_cam_approve_msg(_user.id)
            else:
                _user.is_waiting = True
                self.send_chat_msg(
                    '%s is waiting in the greenroom.' % (_user.nick))

    def do_lockdown(self, soft):

        global password
        global lockdown

        if self.is_client_owner:
            if soft:
                password = None
            else:
                password = self.do_create_password()

            if not self.privacy_.set_guest_mode():
                self.privacy_.set_room_password(password)
                lockdown = True
                if soft:
                    self.send_chat_msg('a0: Lockdown - no guests allowed.')
                else:
                    self.send_chat_msg(
                        'a0: Lockdown - tmp password is: %s' % (password))
            else:
                password = None
                self.privacy_.set_room_password(password)
                lockdown = False
                self.send_chat_msg(
                    'a1: %s is open to the public again.' % (self.room_name))

        else:
            if not pinylib.CONFIG.B_ALLOW_GUESTS:
                lockdown = False
                self.do_guests()
                self.send_chat_msg(
                    'a1: %s is open to the public again.' % (self.room_name))

            else:
                self.do_guests()
                self.send_chat_msg('a0: Lockdown - no guests allowed.')

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

        if uid != self.client_id:
            if self.nick_check(_user.nick):
                if pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN:
                    self.send_kick_msg(uid)
                else:
                    self.send_ban_msg(uid)

                self.console_write(pinylib.COLOR['bright_cyan'], '[User] %s:%s Changed nick to: %s' %
                                   (old_nick, uid, nick))

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
            parts = msg.split(' ')
            cmd = parts[0].lower().strip()
            cmd_arg = ' '.join(parts[1:]).strip()

            _user = self.users.search_by_nick(self.active_user.nick)

            if _user.user_level < 4:
                if cmd == prefix + 'chatmod':
                    self.do_chatmod(cmd_arg)
                elif cmd == prefix + 'rmchatmod':
                    self.do_remove_chatmod(cmd_arg)
                elif cmd == prefix + 'demod':
                    self.do_deop_user(cmd_arg)
                elif cmd == prefix + 'noguest':
                    self.do_guests()
                elif cmd == prefix + 'lockdown':
                    self.do_lockdown(1)
                elif cmd == prefix + 'lockup':
                    self.do_lockdown(0)

            if _user.user_level == 2:

                if cmd == prefix + 'chatadmin':
                    self.do_chatadmin(cmd_arg)

                if self.is_client_owner:

                    if cmd == prefix + 'p2t':
                        threading.Thread(target=self.do_push2talk).start()
                    elif cmd == prefix + 'greet':
                        self.do_greet()
                    elif cmd == prefix == 'kb':
                        self.do_kick_as_ban()
                    elif cmd == prefix + 'reboot':
                        self.do_reboot()
                    elif cmd == prefix + 'dir':
                        threading.Thread(target=self.do_directory).start()
                    elif cmd == prefix + 'addmod':
                        threading.Thread(target=self.do_make_mod,
                                         args=(cmd_arg,)).start()
                    elif cmd == prefix + 'removemod':
                        threading.Thread(
                            target=self.do_remove_mod, args=(cmd_arg,)).start()

            if _user.user_level < 5:

                if cmd == prefix + 'mod':
                    self.do_op_user(cmd_arg)
                elif cmd == prefix + 'who':
                    self.do_user_info(cmd_arg)
                elif cmd == prefix + 'v':
                    self.do_verified(cmd_arg)
                elif cmd == prefix + 'rmv':
                    self.do_remove_verified(cmd_arg)
                elif cmd == prefix + 'clr':
                    self.do_clear()
                elif cmd == prefix + 'forgive':
                    threading.Thread(target=self.do_forgive,
                                     args=(cmd_arg,)).start()
                elif cmd == prefix + 'kick':
                    threading.Thread(target=self.do_kick,
                                     args=(cmd_arg,)).start()
                elif cmd == prefix + 'ban':
                    threading.Thread(target=self.do_ban,
                                     args=(cmd_arg,)).start()
                elif cmd == prefix + 'uinfo':
                    self.do_user_info(cmd_arg)
                elif cmd == prefix + 'cam':
                    self.do_cam_approve(cmd_arg)
                elif cmd == prefix + 'close':
                    self.do_close_broadcast(cmd_arg)
                elif cmd == prefix + 'badn':
                    self.do_bad_nick(cmd_arg)
                elif cmd == prefix + 'rmbadn':
                    self.do_remove_bad_nick(cmd_arg)
                elif cmd == prefix + 'banw':
                    self.do_bad_string(cmd_arg)
                elif cmd == prefix + 'rmw':
                    self.do_remove_bad_string(cmd_arg)
                elif cmd == prefix + 'bada':
                    self.do_bad_account(cmd_arg)
                elif cmd == prefix + 'rmbada':
                    self.do_remove_bad_account(cmd_arg)

                if cmd == prefix + 'dj':
                    threading.Thread(target=self.do_dj,
                                     args=(cmd_arg,)).start()
                elif cmd == prefix + 'djmode':
                    self.do_dj_mode()

            if _user.user_level < 6:

                if dj_mode and _user.account not in djs:
                    isdj = 1
                elif dj_mode and _user.account in djs:
                    isdj = 0

                if cmd == prefix + 'skip':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        self.do_skip()
                elif cmd == prefix + 'media':
                    self.do_media_info()
                elif cmd == prefix + 'yt':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        threading.Thread(
                            target=self.do_play_youtube, args=(cmd_arg,)).start()
                elif cmd == prefix + 'yts':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        threading.Thread(
                            target=self.do_youtube_search, args=(cmd_arg,)).start()
                elif cmd == prefix + 'del':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        self.do_delete_playlist_item(cmd_arg)
                elif cmd == prefix + 'replay':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        self.do_media_replay()
                elif cmd == prefix + 'play':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        self.do_play_media()
                elif cmd == prefix + 'pause':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        self.do_media_pause()
                elif cmd == prefix + 'seek':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        self.do_seek_media(cmd_arg)
                elif cmd == prefix + 'stop':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        self.do_close_media()
                elif cmd == prefix + 'reset':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
                        self.do_clear_playlist()
                elif cmd == prefix + 'next':
                    if dj_mode and isdj:
                        self.send_chat_msg('%s, %s is in DJ mode, current djs are: %s' % (
                            self.active_user.nick, self.room_name, str(djs)))
                    elif dj_mode and not isdj or not dj_mode:
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
                elif cmd == prefix + 'help':
                    self.do_help()
                elif cmd == prefix + 'whatsong':
                    self.do_now_playing()

                if cmd == prefix + 'status':
                    self.do_playlist_status()
                elif cmd == prefix + 'now':
                    self.do_now_playing()
                elif cmd == prefix + 'whoplayed':
                    self.do_who_plays()
                elif cmd == prefix + 'urb':
                    threading.Thread(
                        target=self.do_search_urban_dictionary, args=(cmd_arg,)).start()
                elif cmd == prefix + 'wea':
                    threading.Thread(
                        target=self.do_weather_search, args=(cmd_arg,)).start()
                elif cmd == prefix + 'chuck':
                    threading.Thread(target=self.do_chuck_noris).start()
                elif cmd == prefix + '8ball':
                    self.do_8ball(cmd_arg)
                elif cmd == prefix + 'roll':
                    self.do_dice()
                elif cmd == prefix + 'flip':
                    self.do_flip_coin()

            self.console_write(
                pinylib.COLOR['yellow'], self.active_user.nick + ': ' + cmd + ' ' + cmd_arg)

        else:
            self.console_write(
                pinylib.COLOR['green'], self.active_user.nick + ': ' + msg)

            if self.active_user.user_level > 4:
                threading.Thread(target=self.check_msg, args=(msg,)).start()

        self.active_user.last_msg = msg

    def do_dj(self, account):
        global djs
        _user = self.users.search_by_nick(account)

        if _user is None:
            self.send_chat_msg('%s has no account.' % account)
        else:

            if _user.account in djs:
                djs.remove(_user.account)
                self.send_chat_msg('%s is not longer a dj.' % _user.account)
            else:
                djs.append(_user.account)
                self.send_chat_msg(
                    '%s is now in the DJ crew.' % _user. account)

    def do_dj_mode(self):
        global dj_mode
        if dj_mode == 0:
            dj_mode = 1
            self.send_chat_msg('Focbity is now in DJ mode!')

        else:
            dj_mode = 0
            self.send_chat_msg(
                'DJ mode is off, you can add to the youtube playlist now.')

    def do_make_mod(self, account):
        """
        Make a tinychat account a room moderator.

        :param account: The account to make a moderator.
        :type account: str
        """
        if self.is_client_owner:
            if len(account) is 0:
                self.send_chat_msg('Missing account name.')
            else:
                tc_user = self.privacy_.make_moderator(account)
                if tc_user is None:
                    self.send_chat_msg('The account is invalid.')
                elif not tc_user:
                    self.send_chat_msg('%s is already a moderator.' % account)
                elif tc_user:
                    self.send_chat_msg(
                        '%s was made a room moderator.' % account)

    def do_remove_mod(self, account):
        """
        Removes a tinychat account from the moderator list.

        :param account: The account to remove from the moderator list.
        :type account: str
        """
        if self.is_client_owner:
            if len(account) is 0:
                self.send_chat_msg('Missing account name.')
            else:
                tc_user = self.privacy_.remove_moderator(account)
                if tc_user:
                    self.send_chat_msg(
                        '%s is no longer a room moderator.' % account)
                elif not tc_user:
                    self.send_chat_msg('%s is not a room moderator.' % account)

    def do_directory(self):
        """ Toggles if the room should be shown on the directory. """
        if self.is_client_owner:
            if self.privacy_.show_on_directory():
                self.send_chat_msg('Room IS shown on the directory.')
            else:
                self.send_chat_msg('Room is NOT shown on the directory.')

    def do_push2talk(self):
        """ Toggles if the room should be in push2talk mode. """
        if self.is_client_owner:
            if self.privacy_.set_push2talk():
                self.send_chat_msg('Push2Talk is enabled.')
            else:
                self.send_chat_msg('Push2Talk is disabled.')

    def do_green_room(self):
        """ Toggles if the room should be in greenroom mode. """
        if self.is_client_owner:
            if self.privacy_.set_greenroom():
                self.send_chat_msg('Green room is enabled.')
            else:
                self.send_chat_msg('Green room is disabled.')

    def do_clear_room_bans(self):
        """ Clear all room bans. """
        if self.is_client_owner:
            if self.privacy_.clear_bans():
                self.send_chat_msg('All room bans was cleared.')

    def do_kill(self):
        """ Kills the bot. """
        self.disconnect()

    def do_reboot(self):
        """ Reboots the bot. """
        self.reconnect()

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

    def do_op_user(self, user_name):
        """ 
        Lets the room owner, a mod or a bot controller make another user a bot controller.

        :param user_name: The user to op.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.send_chat_msg('Missing username.')
            else:
                _user = self.users.search_by_nick(user_name)
                if _user is not None:
                    _user.user_level = 4
                    self.send_chat_msg('No user named: %s' % user_name)

    def do_deop_user(self, user_name):
        """ 
        Lets the room owner, a mod or a bot controller remove a user from being a bot controller.

        :param user_name: The user to deop.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.send_chat_msg('Missing username.')
            else:
                _user = self.users.search_by_nick(user_name)

                if _user is not None:

                    if _user.account is not None:
                        _user.user_level == 6
                    else:
                        _user.user_level == 7
                        self.send_chat_msg('No user named: %s' % user_name)

    def do_guests(self):
        """ Toggles if guests are allowed to join the room or not. """
        pinylib.CONFIG.B_ALLOW_GUESTS = not pinylib.CONFIG.B_ALLOW_GUESTS
        self.send_chat_msg('Allow Guests: %s' % pinylib.CONFIG.B_ALLOW_GUESTS)

    def do_greet(self):
        """ Toggles if users should be greeted on entry. """
        pinylib.CONFIG.B_GREET = not pinylib.CONFIG.B_GREET
        self.send_chat_msg('Greet Users: %s' % pinylib.CONFIG.B_GREET)

    def do_kick_as_ban(self):
        """ Toggles if kick should be used instead of ban for auto bans . """
        pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN = not pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN
        self.send_chat_msg('Use Kick As Auto Ban: %s' %
                           pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN)

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

    def do_create_password(self):
        global _KEYWORDS
        word = random.choice(_KEYWORDS)
        numbers = str(randint(100, 999))
        xpassword = word + numbers

        return xpassword

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

    def do_clear(self):
        """ Clears the chat box. """
        self.send_chat_msg('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n'
                           '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

    def do_nick(self, new_nick):
        """ 
        Set a new nick for the bot.

        :param new_nick: The new nick name.
        :type new_nick: str
        """
        if len(new_nick) is 0:
            self.nickname = pinylib.string_util.create_random_string(5, 25)
            self.set_nick()
        else:
            self.nickname = new_nick
            self.set_nick()

    def do_kick(self, user_name):
        """ 
        Kick a user out of the room.

        :param user_name: The username to kick.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.send_chat_msg('Missing username.')
            elif user_name == self.nickname:
                self.send_chat_msg('Action not allowed.')
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
                        self.send_chat_msg('No user named: %s' % user_name)
                    elif _user.user_level < self.active_user.user_level:
                        self.send_chat_msg(
                            'imma let ya guys figure that out...')
                    else:
                        self.send_kick_msg(_user.id)

    def do_forgive(self, nick_name):
        """
        Forgive a user based on if their user id (uid) is found in the room's ban list.
        :param nick_name: str the nick name of the user that was banned.
        """
        global banlist
        forgiven = False

        if self.is_client_mod:
            if len(nick_name) is 0:
                self.send_chat_msg(
                    ' Please state a nick to forgive from the ban list.')
            else:
                for item in banlist['items']:
                    if item['nick'] == nick_name:
                        self.users.delete_banned_user(item)
                        self.send_unban_msg(item['id'])
                        forgiven = True
                    else:
                        self.send_chat_msg(
                            nick_name + ' was not found in the banlist')
                if forgiven:
                    self.send_chat_msg(nick_name + ' was forgiven.')

    def on_banlist(self, banlist_info):
        """
        Return json from servers 
        """

        global banlist
        banlist = banlist_info

    def do_ban(self, user_name):
        """ 
        Ban a user from the room.

        :param user_name: The username to ban.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.send_chat_msg('Missing username.')
            elif user_name == self.nickname:
                self.send_chat_msg('Action not allowed.')
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
                        self.send_chat_msg('No user named: %s' % user_name)
                    elif _user.user_level < self.active_user.user_level:
                        self.send_chat_msg(
                            'i dont wanna be a part of ya problems..')
                    else:
                        self.send_ban_msg(_user.id)

    def do_bad_nick(self, bad_nick):
        """ 
        Adds a username to the nick bans file.

        :param bad_nick: The bad nick to write to the nick bans file.
        :type bad_nick: str
        """
        if self.is_client_mod:
            if len(bad_nick) is 0:
                self.send_chat_msg('Missing username.')
            elif self.nick_check(bad_nick):
                self.send_chat_msg('%s is already in list.' % bad_nick)
            else:
                db = pickledb.load(userdb, False)
                user = {'by': self.active_user.account,
                        'created': time.time(), 'reason': 'NA'}
                db.dadd('badnicks', (bad_nick, user))
                db.dump()
          

                self.send_chat_msg('%s was added to banned nicks.' % bad_nick)

    def do_remove_bad_nick(self, bad_nick):
        """ 
        Removes nick from the nick bans file.

        :param bad_nick: The bad nick to remove from the nick bans file.
        :type bad_nick: str
        """
        if self.is_client_mod:
            if len(bad_nick) is 0:
                self.send_chat_msg('Missing username')
            else:
                if not self.nick_check(bad_nick):
                    self.send_chat_msg(
                        '%s is not in the banned nicks.' % bad_nick)
                else:
                    db = pickledb.load(userdb, False)
                    db.dpop('badnicks', bad_nick)
                    db.dump()
                   
                    self.send_chat_msg(
                        '%s removed from banned nicks.' % bad_nick)

    def do_bad_string(self, bad_string):
        """ 
        Adds a string to the string bans file.

        :param bad_string: The bad string to add to the string bans file.
        :type bad_string: str
        """
        if self.is_client_mod:
            if len(bad_string) is 0:
                self.send_chat_msg('Ban string can\'t be blank.')
            elif len(bad_string) < 3:
                self.send_chat_msg(
                    'Ban string to short: ' + str(len(bad_string)))
            elif self.word_check(bad_string):
                self.send_chat_msg('%s is already in list.' % bad_string)
            else:
                db = pickledb.load(userdb, False)
                user = {'by': self.active_user.account,
                        'created': time.time(), 'reason': 'NA'}
                db.dadd('badwords', (bad_string, user))
                db.dump()
           
                self.send_chat_msg(
                    '%s was added to banned words.' % bad_string)

    def do_remove_bad_string(self, bad_string):
        """ 
        Removes a string from the string bans file.

        :param bad_string: The bad string to remove from the string bans file.
        :type bad_string: str
        """
        if self.is_client_mod:
            if len(bad_string) is 0:
                self.send_chat_msg('Missing word string.')
            else:

                if not self.word_check(bad_string):
                    self.send_chat_msg('%s is not banned.' % bad_string)

                else:
                    db = pickledb.load(userdb, False)
                    db.dpop('badwords', bad_string)
                    db.dump()

                    self.send_chat_msg(
                        '%s was removed to banned words.' % bad_string)

    def do_bad_account(self, bad_account_name):
        """ 
        Adds an account name to the account bans file.

        :param bad_account_name: The bad account name to add to the account bans file.
        :type bad_account_name: str
        """

        if self.is_client_mod:
            if len(bad_account_name) is 0:
                self.send_chat_msg('Account can\'t be blank.')
            elif len(bad_account_name) < 3:
                self.send_chat_msg('Account to short: ' +
                                   str(len(bad_account_name)))
            elif self.user_check(bad_account_name) == 9:
                self.send_chat_msg('%s is already in list.' % bad_account_name)
            else:

                db = pickledb.load(userdb, False)
                if self.user_check(bad_account_name) > 0:
                    db.dpop('users', bad_account_name)

                user = {'level': 9, 'by': self.active_user.account,
                        'created': time.time(), 'reason': 'NA'}
                db.dadd('users', (bad_account_name, user))
                db.dump()
           

                self.send_chat_msg(
                    '%s was added to banned accounts.' % bad_account_name)

    def do_remove_bad_account(self, bad_account):
        """ 
        Removes an account from the account bans file.

        :param bad_account: The badd account name to remove from account bans file.
        :type bad_account: str
        """
        if self.is_client_mod:
            if len(bad_account) is 0:
                self.send_chat_msg('Missing account.')
            else:
                if self.user_check(bad_account) == 9:
                    db = pickledb.load(userdb, False)
                    db.dpop('users', bad_account)
                    db.dump()
                 
                    self.send_chat_msg(
                        '%s is not in banned accounts.' % bad_account)

    def do_verified(self, verified_name):

        if self.is_client_mod:
            if len(verified_name) is 0:
                self.send_chat_msg('Account can\'t be blank.')
            elif len(verified_name) < 3:
                self.send_chat_msg('Account too short: ' +
                                   str(len(verified_name)))
            elif self.user_check(verified_name) == 5:
                self.send_chat_msg('%s is already in list.' % verified_name)
            else:
                db = pickledb.load(userdb, False)
                if self.user_check(verified_name) == 5:
                    db.dpop('users', verified_name)

                user = {'level': 5, 'by': self.active_user.account,
                        'created': time.time()}
                db.dadd('users', (verified_name, user))
                db.dump()
             

                self.console_write(pinylib.COLOR['cyan'], '[User] New account %s, verified by %s' % (
                    verified_name, self.active_user.account))

                self.send_chat_msg('%s account is verified.' % verified_name)

    def do_remove_verified(self, verified_account):

        if self.is_client_mod:
            if len(verified_account) is 0:
                self.send_chat_msg('Missing account.')
            else:
                db = pickledb.load(userdb, False)
                if self.user_check(verified_account) == 5:
                    db.dpop('users', verified_account)
                    db.dump()
               

                    self.send_chat_msg(
                        'Account %s was removed from verified accounts.' % verified_account)
                else:
                    self.send_chat_msg(
                        'Account %s is not verified accounts.' % verified_account)

    def user_check(self, account):

        if db.dexists('users', account):
            user = db.dget('users', account)
            return user['level']
        else:
            return 0

    def word_check(self, word):

        if db.dexists('badwords', word):
            user = db.dget('badwords', word)
            return True
        else:
            return False

    def nick_check(self, nick):

        if db.dexists('badnicks', nick):
            user = db.dget('badnicks', nick)
            return True
        else:
            return False

    def do_chatmod(self, verified_name):

        if self.is_client_mod:
            if len(verified_name) is 0:
                self.send_chat_msg('Account can\'t be blank.')
            elif len(verified_name) < 3:
                self.send_chat_msg('Account too short: ' +
                                   str(len(verified_name)))
            elif self.user_check(verified_name) == 4:
                self.send_chat_msg('%s is already in list.' % verified_name)
            else:

                db = pickledb.load(userdb, False)
                if self.user_check(verified_name) == 5:
                    db.dpop('users', verified_name)

                user = {'level': 4, 'by': self.active_user.account,
                        'created': time.time()}
                db.dadd('users', (verified_name, user))
                db.dump()
               

                self.send_chat_msg('%s is a chatmod now.' % verified_name)

    def do_remove_chatmod(self, verified_account):
        if self.is_client_mod:
            if len(verified_account) is 0:
                self.send_chat_msg('Missing account.')
            else:

                if self.user_check(verified_account) == 4:
                    db = pickledb.load(userdb, False)
                    db.dpop('users', verified_account)
                    db.dump()

                    self.send_chat_msg(
                        '%s is not a chatmod anymore.' % verified_account)
                else:
                    self.send_chat_msg(
                        'Account %s is not chatmod accounts.' % verified_account)

    def do_chatadmin(self, verified_name):

        if self.is_client_mod:
            if len(verified_name) is 0:
                self.send_chat_msg('Account can\'t be blank.')
            elif len(verified_name) < 3:
                self.send_chat_msg('Account too short: ' +
                                   str(len(verified_name)))

            elif self.user_check(verified_name) == 2:
                self.send_chat_msg('%s is already in list.' % verified_name)
            else:
                db = pickledb.load(userdb, False)
                if self.user_check(verified_name) == 4 or self.user_check(verified_name) == 3 or self.user_check(verified_name) == 5:
                    db.dpop('users', verified_name)

                user = {'level': 2, 'by': self.active_user.account,
                        'created': time.time()}
                db.dadd('users', (verified_name, user))
                db.dump()
                
                self.send_chat_msg('%s is an admin now.' % verified_name)

    def do_remove_chatadmin(self, verified_account):
        if self.is_client_mod:
            if len(verified_account) is 0:
                self.send_chat_msg('Missing account.')
            else:

                if self.user_check(verified_account) == 2:
                    db = pickledb.load(userdb, False)
                    db.dpop('users', verified_account)
                    db.dump()
                   
                    self.send_chat_msg(
                        '%s is not an admin anymore.' % verified_account)

    def do_cam_approve(self, user_name):
        """
        Allow a user to broadcast in a green room enabled room.

        :param user_name:  The name of the user allowed to broadcast.
        :type user_name: str
        """
        _user = self.users.search_by_nick(user_name)
        if len(user_name) > 0:
            if _user.is_waiting:
                self.send_cam_approve_msg(_user.id)
                _user.is_broadcasting = True
        else:
            self.send_chat_msg('No user named: %s' % user_name)

    def do_close_broadcast(self, user_name):
        """
        Close a users broadcast.

        :param user_name: The name of the user to close.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) == 0:
                self.send_chat_msg('Mising user name.')
            else:
                _user = self.users.search_by_nick(user_name)
                if _user is not None and _user.is_broadcasting:
                    self.send_close_user_msg(_user.id)
                else:
                    self.send_chat_msg('No user named: %s' % user_name)

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
                    self.send_private_msg(self.active_user.id,
                                          '(%s) %s %s' % (self.playlist.current_index, track.title,
                                                          self.format_time(track.time)))
                else:
                    self.send_private_msg(self.active_user.id, '%s %s' %
                                          (track.title, self.format_time(track.time)))
            else:
                self.send_private_msg(
                    self.active_user.nick, 'No track playing.')

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

    def do_help(self):
        """ Posts a link to github readme/wiki or other page about the bot commands. """

        if self.active_user.user_level < 5:
            time.sleep(1)
            self.send_private_msg(
                self.active_user.id, 'Mod Cmds: !clr, !kick, !ban, !cam, !close, !bada  <account>, !banw <badword>,!rmw <badword>, !rmbad <account>, !badn <nick>, !rmv, !v')
        if self.active_user.user_level == 5:
            time.sleep(4)
            self.send_private_msg(
                self.active_user.id, 'Media Cmds: !yt, !close, !seek, !reset, !spl, !del, !skip, !yts, !rpl, !pause, !play, !pyst')
        if self.active_user.user_level < 4:
            time.sleep(1)
            self.send_private_msg(
                self.active_user.id, 'Admin Cmds: !lockdown (noguests), !lockup(password enabled), !chatmod, !dechatmode, !noguest')

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
                    self.send_chat_msg(
                        'Could not find a definition for: %s' % search_str)
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
                self.send_chat_msg(
                    'Could not find weather data for: %s' % search_str)
            else:
                self.send_chat_msg(weather)

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

    def private_message_handler(self, private_msg):
        """
        Private message handler.

        Overrides private_message_handler in pinylib
        to enable private commands.

        :param private_msg: The private message.
        :type private_msg: str
        """
        prefix = pinylib.CONFIG.B_PREFIX
        # Split the message in to parts.
        pm_parts = private_msg.split(' ')
        # parts[0] is the command..
        pm_cmd = pm_parts[0].lower().strip()
        # The rest is a command argument.
        pm_arg = ' '.join(pm_parts[1:]).strip()

        if self.is_client_owner:

            if pm_cmd == prefix + 'help':
                self.do_help()
            elif pm_cmd == prefix + 'clrbn':
                self.do_clear_bad_nicks()

            elif pm_cmd == prefix + 'clrbs':
                self.do_clear_bad_strings()

            elif pm_cmd == prefix + 'clrba':
                self.do_clear_bad_accounts()

        self.console_write(pinylib.COLOR['white'], '[MSG] Private message from %s: %s' % (
            self.active_user.nick, private_msg))

    def on_quitting(self, uid, account):

        if account in botnet:
            botnet.remove(account)
            self.console_write(
                pinylib.COLOR['bright_yellow'], '[Botnet] Bot: %s unregistered.' % (account))
            del botnet[:]
            bots = False

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

    def check_msg(self, msg):
        """ 
        Checks the chat message for ban string.

        :param msg: The chat message.
        :type msg: str
        """

        global lastmsgs
        global spam
        global spammer

        should_be_banned = False
        is_a_spammer = False

        chat_words = msg.split(' ')

        # if flooded or a long text

        total = sum(char.isspace() or char == "0" for char in msg)

        if total > 140 and self.active_user.nick == spammer:
            spammer = 0
            self.console_write(pinylib.COLOR[
                               'bright_yellow'], '[Security] Spam - banned %s.' % (self.active_user.nick))
            if self.active_user.user_level > 4:
                self.send_ban_msg(self.active_user.id)
        elif total > 140:
            spammer = self.active_user.nick
            self.console_write(pinylib.COLOR[
                               'bright_yellow'], '[Security] Spam: Long message - %s by %s' % (total, self.active_user.nick))
            if self.active_user.user_level > 4:
                self.send_kick_msg(self.active_user.id)

        for word in chat_words:
            if self.word_check(word):
                should_be_banned = True

        if self.active_user.user_level > 5:

            if len(lastmsgs) is 0:
                lastmsgs.append(msg)
                self.console_write(
                    pinylib.COLOR['bright_yellow'], '[Security] Spam: Protection on.')

            else:
                msg_count = str(len(lastmsgs))
                self.console_write(pinylib.COLOR[
                                   'bright_yellow'], '[Security] Spam: Processing - %s' % (msg_count))

                if msg in lastmsgs:
                    spam += 1
                    lastmsgs.append(msg)
                    spammer = self.active_user.nick
                    self.console_write(pinylib.COLOR[
                                       'bright_yellow'], '[Security] Spam: Found Spammer %s' % (self.active_user.nick))
                else:
                    lastmsgs.append(msg)

            if spam > 2:
                should_be_banned = True
                is_a_spammer = True
                spammer = 0
                spam = 0
                del lastmsgs[:]
                lastmsgs = []

            if len(lastmsgs) > 8:
                del lastmsgs[:]
                lastmsgs = []
                spam = 0
                spammer = 0
                self.console_write(
                    pinylib.COLOR['bright_yellow'], '[Security] Spam: Resetting last message db.')

        if should_be_banned:
            if self.active_user.user_level == 6:
                if is_a_spammer:
                    self.do_bad_account(self.active_user.account)
                    is_a_spammer = False
                self.send_ban_msg(self.active_user.id)
            elif len(self.active_user.account) is 0:
                if is_a_spammer:
                    is_a_spammer = False
                self.send_ban_msg(self.active_user.id)

            self.console_write(pinylib.COLOR['cyan'], '[Security] Spam: Flood, Repeat or Badword by %s' % (self.active_user.nick))






