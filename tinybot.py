# -*- coding: utf-8 -*-
""" Tinybot by Nortxort (https://github.com/nortxort/tinybot-rtc) """
""" Modified by odsum (https://github.com/odsum/buddytinychatbot) """

import time
import logging
import threading
import pinylib
from util import tracklist
from apis import youtube, other, locals_
from Crypto.Hash import MD5

import socket
import random
from random import randint

import pickle
import gib_detect_train
import base64

__version__ = '1.1-Buddy'

log = logging.getLogger(__name__)

joind_time = 0
joind_count = 0
autoban_time = 0
autoban_count = 0
newnick = 0
botnet = []
ban_time = 0
vote_id = 0
vote_time = 0
vote_count = 0
voters = 0
lastmsgs = []
spam = 0
spammer = 0
djs = []
dj_mode = 0

model_data = pickle.load(open('gib_model.pki', 'rb'))

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
    
    global bots
    global bot_master
    global hub
    global hub_host
    global hub_port
    global key
    global model_mat
    global threshold
    global lockdown

    model_mat = model_data['mat']
    threshold = model_data['thresh']

    key = pinylib.CONFIG.B_HUB_KEY

    lockdown = False
    bots = False
    bot_master = pinylib.CONFIG.B_BOT_MASTER

    hub = pinylib.CONFIG.B_BOT_HUB
   
    if hub:
    	hub_host = pinylib.CONFIG.B_BOT_HUB_HOST
   	hub_port = pinylib.CONFIG.B_BOT_HUB_PORT
    	if hub_host == '':
		hub_host = socket.gethostname()   	

    def encode(self, clear):
	enc = []
    	for i in range(len(clear)):
        	key_c = key[i % len(key)]
        	enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        	enc.append(enc_c)
    	return base64.urlsafe_b64encode("".join(enc))

    def decode(self, enc):
	dec = []
    	enc = base64.urlsafe_b64decode(enc)
    	for i in range(len(enc)):
        	key_c = key[i % len(key)]
        	dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        	dec.append(dec_c)
    	return "".join(dec)	

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
        self.console_write(pinylib.COLOR['bright_green'], 'Client joined the room: %s:%s' % (client.nick, client.id))

        threading.Thread(target=self.options).start()

    def on_join(self, join_info):
        """
        Received when a user joins the room.

        :param join_info: This contains user information such as role, account and so on.
        :type join_info: dict
        """

  	global joind_time 
        global joind_count
        global autoban_time
        global bots
	global bot_master
	global lockdown
    	global model_mat
    	global threshold

        time_join = time.time()

        log.info('user join info: %s' % join_info)
        _user = self.users.add(join_info)
	
    	spamnick = gib_detect_train.avg_transition_prob(_user.nick, model_mat) > threshold

	if len(_user.nick) > 5 and spamnick == 0:
        
		if _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
			pass
		elif _user.account in pinylib.CONFIG.B_ACCOUNT_VERIFIED and _user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
			pass
		elif len(_user.account) is not 0 and _user.account not in pinylib.CONFIG.B_ACCOUNT_VERIFIED or len(_user.account) is not 0 and _user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
			pass
                elif len(_user.account) is 0:
                	self.send_ban_msg(_user.id)
                	self.console_write(pinylib.COLOR['cyan'], 'Spam: Random Nick')


        if _user.nick in pinylib.CONFIG.B_NICK_BANS:
		if bots == 1 and bot_master == 1 or bots == 0: 
                	if pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN:
                    		self.send_kick_msg(_user.id)
        		else:
                   		self.send_ban_msg(_user.id)
		self.console_write(pinylib.COLOR['cyan'], 'Banned: Nick %s' % (_user.nick))
	
        if _user.account:
            if _user.is_owner:
                _user.user_level = 1
                self.console_write(pinylib.COLOR['red'], 'Room Owner %s:%d:%s' %
                                   (_user.nick, _user.id, _user.account))
            elif _user.is_mod:
		
                _user.user_level = 3
                self.console_write(pinylib.COLOR['bright_red'], 'Moderator %s:%d:%s' %
                                   (_user.nick, _user.id, _user.account))
            else:

                self.console_write(pinylib.COLOR['bright_yellow'], '%s:%d has account: %s' %
                                   (_user.nick, _user.id, _user.account))

	        if _user.account in pinylib.CONFIG.B_ACCOUNT_BANS and self.is_client_mod:
			if bots == 1 and bot_master == 1 or bots == 0: 
                    		if pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN:
                        		self.send_kick_msg(_user.id)
                    		else:
                        		self.send_ban_msg(_user.id)
			self.console_write(pinylib.COLOR['cyan'], 'Banned: Account %s' % (_user.account))

                else:

                    tc_info = pinylib.apis.tinychat.user_info(_user.account)
                    if tc_info is not None:
                        _user.tinychat_id = tc_info['tinychat_id']
                        _user.last_login = tc_info['last_active']
		
		if _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
			_user.user_level = 4

        if lockdown:

                            if time_join - 180  > autoban_time:		
                                
                                if bots == 1 and bot_master == 1 or bots == 0:
				    if hub and lockdown == 1:
					soft = 1
				    	self.do_lockdown(soft)
				    elif not hub and lockdown == 1:
					if pinylib.CONFIG.B_ALLOW_GUESTS:		
						self.do_guests()

	  				self.send_chat_msg('a1: Fobcity is open to the public again.')
					lockdown = False	

				autoban_time = 0
                                self.console_write(pinylib.COLOR['cyan'], 'Lockdown Mode Reset')
	else:

		maxtime = 10
       		maxjoins = 7
        			
        	if joind_time == 0:
			joind_time  = time.time()
			joind_count += 1

        	elif time_join - joind_time > maxtime:
			joind_count = 0
			joind_time  = 0
                            
        	elif joind_count > maxjoins:
                                    
                	if bots == 1 and bot_master == 1 or bots == 0:
				if hub and lockdown == 0:
					soft = 0
					self.do_lockdown(soft)
				elif not hub and lockdown == 0:
					if pinylib.CONFIG.B_ALLOW_GUESTS:		
						self.do_guests()

                                	self.send_chat_msg('a0: Lockdown - No guest mode')

	                autoban_time = time_join
                        self.console_write(pinylib.COLOR['cyan'], 'Lockdown started %' % (time_join))
        	else:
                        joind_count += 1

	if not pinylib.CONFIG.B_ALLOW_GUESTS:		
				if bots == 1 and bot_master == 0 or bots == 0:
					if _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
							pass
					elif _user.account in pinylib.CONFIG.B_ACCOUNT_VERIFIED and _user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
							pass
					elif len(_user.account) is not 0 and _user.account not in pinylib.CONFIG.B_ACCOUNT_VERIFIED or len(_user.account) is not 0 and _user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
							pass
                			elif len(_user.account) is 0:
                					self.send_ban_msg(_user.id)
    							self.console_write(pinylib.COLOR['cyan'], '%s was banned on no guest mode' % (_user.nick))
	
    	self.console_write(pinylib.COLOR['cyan'], '%s:%d joined the room. (%s)' % (_user.nick, _user.id, joind_count))
        threading.Thread(target=self.welcome, args=(_user.id,)).start()

     
    def welcome(self, uid):
	time.sleep(5)
        _user = self.users.search(uid)

	if _user is not None: 
		if pinylib.CONFIG.B_ALLOW_GUESTS:
        			if pinylib.CONFIG.B_GREET and _user is not None:
					if bots == 1 and bot_master == 1 or bots == 0:
            					if not _user.nick.startswith('guest-'):
							if _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
								self.send_private_msg(_user.id, 'You have chat mod access - !help')
							elif _user.account in pinylib.CONFIG.B_ACCOUNT_VERIFIED and _user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD: 	
								self.send_private_msg(_user.id, 'You are verified, you add to the Youtube social playlist via !yt - Other cmds type !help')
							elif len(_user.account) is not 0 and _user.account not in pinylib.CONFIG.B_ACCOUNT_VERIFIED or len(_user.account) is not 0  and _user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
								self.send_private_msg(_user.id, 'Welcome to Fobcity - ask to have your account verified.')
                					elif len(_user.account) is 0:
								self.send_private_msg(_user.id, 'Welcome to Fobcity - we suggest making an account, personal info trolling or sexual harassment will not be tolerated.')

    def on_pending_moderation(self, pending):
	if bots == 1 and bot_master == 0 or bots == 0:
        	_user = self.users.search(pending['handle'])
        	if _user is not None:
            		if _user.account in pinylib.CONFIG.B_ACCOUNT_VERIFIED:
		   		self.send_cam_approve_msg( _user.id)
	    		else:
	            		_user.is_waiting = True
		   		self.send_chat_msg('%s is waiting in the greenroom.' % (_user.nick))
  
    def do_push2talk(self):

	       if bots == 1 and bot_master == 1 or bots == 0:
		if hub:
		        cmd = 'donkeykong:0:0'
			l = self.talk_hub(cmd)
			if l == 'error':
  				self.send_chat_msg('Request failed, Hub is offline!')
			else:
       				if int(l) == 0:
  					self.send_chat_msg('Push to talk is enabled.')
                			self.console_write(pinylib.COLOR['cyan'], 'Push2Talk Enabled.')
       				else:
  					self.send_chat_msg('Push to talk is disabled.')
                			self.console_write(pinylib.COLOR['cyan'], 'Push2Talk Disabled.')


    def do_lockdown(self, soft):
       global password
       global lockdown
       if bots == 1 and bot_master == 1 or bots == 0:

		if hub:
			if soft:
				password = 'None'
			else:
				password = self.do_create_password()
		        cmd = 'hellomonkey:'+password
			l = self.talk_hub(cmd)
			if l == 'error':
  				self.send_chat_msg('Hub is offline, manual noguest mode.')
				#fallback
				if not lockdown:
					if pinylib.CONFIG.B_ALLOW_GUESTS:
	                			self.do_guests()
					lockdown = True
  					self.send_chat_msg('a0: Lockdown - no guests allowed')

				else:
					if not pinylib.CONFIG.B_ALLOW_GUESTS:
	                			self.do_guests()

					lockdown = False
  					self.send_chat_msg('a1: Fobcity is open to the public again.')

			else:
       				if int(l) == 0:
					time.sleep(1.0)
					if soft:
  						self.send_chat_msg('a0: Lockdown - no guests allowed')
					else:
  						self.send_chat_msg('a0: Lockdown - tmp password is: %s' % (password))
	
                			self.console_write(pinylib.COLOR['cyan'], 'Guest mode deactivated')
					lockdown = True

       				else:
  					self.send_chat_msg('a1: Fobcity is open to the public again.')
                			self.console_write(pinylib.COLOR['cyan'], 'Guest mode activated')
					lockdown = False

					if not pinylib.CONFIG.B_ALLOW_GUESTS:
	                			self.do_guests()
		

    def talk_hub(self, cmd):

       	host = hub_host 
       	port = hub_port
       	self.console_write(pinylib.COLOR['cyan'], 'Hub: Trying to connect to %s:%s'% (host, port))
       	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	cmd = self.encode(cmd)

	try:
		s.connect((host, port))
	except socket.error, e:
       		self.console_write(pinylib.COLOR['cyan'], 'Hub: error:  %s' % (e))
		data = 'error'
	else:
       		self.console_write(pinylib.COLOR['cyan'], 'Hub: Sent request:  %s' % (cmd))
       		s.send(cmd)
       		data = s.recv(1024)
       		s.close()
	
       	self.console_write(pinylib.COLOR['cyan'], 'Hub: Recieved:  %s' % (data))
	return data

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

    	spamnick = gib_detect_train.avg_transition_prob(_user.nick, model_mat) > threshold

 	if len(_user.nick) > 5 and spamnick == 0:
		if _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
			pass
		elif _user.account in pinylib.CONFIG.B_ACCOUNT_VERIFIED and _user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
			pass
		elif len(_user.account) is not 0 and _user.account not in pinylib.CONFIG.B_ACCOUNT_VERIFIED or len(_user.account) is not 0 and _user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
			pass
                elif len(_user.account) is 0:
                	self.send_ban_msg(_user.id)
                	self.console_write(pinylib.COLOR['cyan'], 'Spam: Random Nick')

        if uid != self.client_id:
            if _user.nick in pinylib.CONFIG.B_NICK_BANS:
                if pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN:
                    self.send_kick_msg(uid)
                else:
                    self.send_ban_msg(uid)

                self.console_write(pinylib.COLOR['bright_cyan'], '%s:%s Changed nick to: %s' %
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
            self.console_write(pinylib.COLOR['bright_magenta'], '%s started youtube video (%s)' %
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
                self.console_write(pinylib.COLOR['bright_magenta'], '%s searched the youtube video to: %s' %
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
                self.console_write(pinylib.COLOR['bright_magenta'], '%s paused the video at %s' %
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


            if self.has_level(3):
 		if bots == 1 and bot_master == 1 or bots == 0:
                	if cmd == prefix + 'chatmod':
                    		self.do_chatmod(cmd_arg)
                    	elif cmd == prefix + 'amod':
                        	threading.Thread(target=self.do_make_mod, args=(cmd_arg,)).start()
                    	elif cmd == prefix + 'ramod':
                        	threading.Thread(target=self.do_remove_mod, args=(cmd_arg,)).start()
                   	elif cmd == prefix + 'dir':
                        	threading.Thread(target=self.do_directory).start()
                	elif cmd == prefix + 'rmchatmod':
                    		self.do_remove_chatmod(cmd_arg)
                    	elif cmd == prefix + 'p2t':
                        	self.do_push2talk()
                	elif cmd == prefix + 'reboot':
                    		self.do_reboot()
                	elif cmd == prefix + 'demod':
                    		self.do_deop_user(cmd_arg)
                	elif cmd == prefix + 'noguest':
                    		self.do_guests()
                	elif cmd == prefix + 'greet':
                    		self.do_greet()
                	elif cmd == prefix == 'kb':
                    		self.do_kick_as_ban()
                	elif cmd == prefix + 'lockdown':
			        soft = 1
                    		self.do_lockdown(soft)
                	elif cmd == prefix + 'lockup':
				soft = 0
                    		self.do_lockdown(soft)

            if self.has_level(3) or _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
 		if bots == 1 and bot_master == 1 or bots == 0:
     
	        	if cmd == prefix + 'mod':
                    		self.do_op_user(cmd_arg)
                	elif cmd == prefix + 'v':
                    		self.do_verified(cmd_arg)
                	elif cmd == prefix + 'rmv':
                    		self.do_remove_verified(cmd_arg)

	    if self.has_level(4) or self.has_level(3) or _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
		 if bots == 1 and bot_master == 1 or bots == 0:       
	
                	if cmd == prefix + 'clr':
                    		self.do_clear()	
			elif cmd == prefix + 'forgive':
                    		threading.Thread(target=self.do_forgive, args=(cmd_arg,)).start()
                	elif cmd == prefix + 'kick':
                    		threading.Thread(target=self.do_kick, args=(cmd_arg,)).start()
                	elif cmd == prefix + 'ban':
                    		threading.Thread(target=self.do_ban, args=(cmd_arg,)).start()
                	elif cmd == prefix + 'uinfo':
                    		self.do_user_info(cmd_arg)
                	elif cmd == prefix + 'cam':
                    		self.do_cam_approve(cmd_arg)
                	elif cmd == prefix + 'close':
                    		self.do_close_broadcast(cmd_arg)

		 if bots == 1 and bot_master == 0 or bots == 0:       
                	if cmd == prefix + 'dj':
                    		threading.Thread(target=self.do_dj, args=(cmd_arg,)).start()
                	elif cmd == prefix + 'djmode':
                    		self.do_dj_mode()


		 if bots == 1 and bot_master == 1 or bots == 0:
			if cmd == prefix + 'badn':
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


	    if _user.account in pinylib.CONFIG.B_ACCOUNT_VERIFIED or self.has_level(4) or self.has_level(3):


				if dj_mode and _user.account not in djs:
					isdj = 1
				elif dj_mode and _user.account in djs:
					isdj = 0					
		 		if bots == 1 and bot_master == 0 or bots == 0:	

	                  		if cmd == prefix + 'skip':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
							self.do_skip()
                			elif cmd == prefix + 'media':
                    				self.do_media_info()
                			elif cmd == prefix + 'yt':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					threading.Thread(target=self.do_play_youtube, args=(cmd_arg,)).start()
               				elif cmd == prefix + 'yts':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					threading.Thread(target=self.do_youtube_search, args=(cmd_arg,)).start()
                			elif cmd == prefix + 'del':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					self.do_delete_playlist_item(cmd_arg)
                			elif cmd == prefix + 'replay':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					self.do_media_replay()
                			elif cmd == prefix + 'play':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					self.do_play_media()
                			elif cmd == prefix + 'pause':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					self.do_media_pause()
                			elif cmd == prefix + 'seek':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					self.do_seek_media(cmd_arg)
                			elif cmd == prefix + 'stop':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					self.do_close_media()
                			elif cmd == prefix + 'reset':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                    					self.do_clear_playlist()
	            			elif cmd == prefix + 'next':
						if dj_mode and isdj:
  							self.send_chat_msg('%s, Focbity is in DJ mode, current djs are: %s' % (self.active_user.nick, str(djs)))
						elif dj_mode and not isdj or not dj_mode:
                 					self.do_next_tune_in_playlist()

                			elif cmd == prefix + 'playlist':
                    				self.do_playlist_info()
                			elif cmd == prefix + 'pyts':
                    				self.do_play_youtube_search(cmd_arg)
                			elif cmd == prefix + 'pls':
                    				threading.Thread(target=self.do_youtube_playlist_search, args=(cmd_arg,)).start()
                			elif cmd == prefix + 'plp':
                    				threading.Thread(target=self.do_play_youtube_playlist, args=(cmd_arg,)).start()
                			elif cmd == prefix + 'ssl':
                    				self.do_show_search_list()
                			elif cmd == prefix + 'help':
                    				self.do_help()
                			elif cmd == prefix + 'whatsong':
                    				self.do_now_playing()


	    
	    if bots == 1 and bot_master == 0 or bots == 0:

	    	if cmd == prefix + 'status':
                 	self.do_playlist_status()
	    	elif cmd == prefix + 'now':
                 	self.do_now_playing()
            	elif cmd == prefix + 'whoplayed':
                 	self.do_who_plays()
                elif cmd == prefix + 'urb':
                  	threading.Thread(target=self.do_search_urban_dictionary, args=(cmd_arg,)).start()
                elif cmd == prefix + 'wea':
                  	threading.Thread(target=self.do_weather_search, args=(cmd_arg,)).start()
                elif cmd == prefix + 'chuck':
                 	threading.Thread(target=self.do_chuck_noris).start()
                elif cmd == prefix + '8ball':
                	self.do_8ball(cmd_arg)
                elif cmd == prefix + 'roll':
                	self.do_dice()
	        elif cmd == prefix + 'flip':
                	self.do_flip_coin()
            self.console_write(pinylib.COLOR['yellow'], self.active_user.nick + ': ' + cmd + ' ' + cmd_arg)
        else:
            self.console_write(pinylib.COLOR['green'], self.active_user.nick + ': ' + msg)

            if self.active_user.user_level > 4:
                	threading.Thread(target=self.check_msg, args=(msg,)).start()
	
	threading.Thread(target=self.check_lockstatus, args=(msg,)).start()  
        self.active_user.last_msg = msg


    def do_dj(self,account):
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
  			self.send_chat_msg('%s is now in the DJ crew.' %_user. account)


    def do_dj_mode (self):
	global dj_mode
	if dj_mode == 0:
		dj_mode = 1
  		self.send_chat_msg('Focbity is now in DJ mode!')

	else: 
		dj_mode = 0
  		self.send_chat_msg('DJ mode is off, you can add to the youtube playlist now.')

    def do_make_mod(self, account):
	pass
    def do_remove_mod(self, account):
	pass
    def do_directory(self):
	pass
    def do_green_room(self):
	pass
    def do_clear_room_bans(self):
	pass
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
                'Remaining Track Time: ' + self.format_time(self.playlist.remaining)
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
			if bots == 1 and bot_master == 1 or bots == 0: 
                    		self.send_chat_msg('%s is now a tmp. mod' % user_name)
                else:
		    	if bots == 1 and bot_master == 1 or bots == 0: 
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
                   _user.user_level = 5
		   if bots == 1 and bot_master == 1 or bots == 0:
			self.send_chat_msg('%s is not a mod anymore' % user_name)
                else:
		   if bots == 1 and bot_master == 0 or bots == 0: 
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
        self.send_chat_msg('Use Kick As Auto Ban: %s' % pinylib.CONFIG.B_USE_KICK_AS_AUTOBAN)


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
                    _ = '\n'.join('(%s) %s' % (i, d['playlist_title']) for i, d in enumerate(self.search_list))
                    self.send_chat_msg(_)
                else:
                    self.send_chat_msg('Failed to find playlist matching search term: %s' % search_str)

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
                        self.send_chat_msg('Please wait while creating playlist..')
                        tracks = youtube.playlist_videos(self.search_list[int_choice])
                        if len(tracks) > 0:
                            self.playlist.add_list(self.active_user.nick, tracks)
                            self.send_chat_msg('Added %s tracks from youtube playlist.' % len(tracks))
                            if not self.playlist.has_active_track:
                                track = self.playlist.next_track
                                self.send_yut_play(track.id, track.time, track.title)
                                self.timer(track.time)
                        else:
                            self.send_chat_msg('Failed to retrieve videos from youtube playlist.')
                    else:
                        self.send_chat_msg('Please make a choice between 0-%s' % str(len(self.search_list) - 1))
            else:
                self.send_chat_msg('The search list does not contain any youtube playlist id\'s.')

    def do_show_search_list(self):
        """ Show what the search list contains. """
        if self.is_client_mod:
            if len(self.search_list) == 0:
                self.send_chat_msg('The search list is empty.')
            elif self.is_search_list_yt_playlist:
                _ = '\n'.join('(%s) - %s' % (i, d['playlist_title']) for i, d in enumerate(self.search_list))
                self.send_chat_msg('Youtube Playlist\'s\n' + _)
            else:
                _ = '\n'.join('(%s) %s %s' % (i, d['video_title'], self.format_time(d['video_time']))
                              for i, d in enumerate(self.search_list))
                self.send_chat_msg('Youtube Tracks\n' + _)

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
                self.send_yut_play(next_track.id, next_track.time, next_track.title)
                self.timer(next_track.time)

    def do_delete_playlist_item(self, to_delete):  # TODO: Make sure this is working.
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
                        temp_indexes = range(range_indexes[0], range_indexes[1] + 1)
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
                            self.send_chat_msg('Deleted %s' % result['track_title'])
                        else:
                            self.send_chat_msg('Deleted tracks at index: %s' %
                                               ', '.join(result['deleted_indexes']))
                    else:

                        self.send_chat_msg('Nothing was deleted.')

    def do_create_password(self):
	_KEYWORDS = ["fob","fobcity","terima","halal","haram","roses",]
	word = random.choice(_KEYWORDS)	
	numbers = str(randint(100, 999))			
	xpassword = word+numbers

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
                self.send_yut_pause(track.id, track.time, self.playlist.elapsed)

    def do_close_media(self):
        """ Close a track playing. """
        if self.is_client_mod:
            if self.playlist.has_active_track:
                self.cancel_timer()
                self.playlist.stop()
                self.send_yut_stop(self.playlist.track.id, self.playlist.track.time, self.playlist.elapsed)

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
                                self.send_yut_pause(track.id, track.time, offset)
                            else:
                                self.playlist.play(offset)
                                self.send_yut_play(track.id, track.time, track.title, offset)
                                self.timer(self.playlist.remaining)

    def do_clear_playlist(self):
        """ Clear the playlist for items."""
        if self.is_client_mod:
            if len(self.playlist.track_list) > 0:
                pl_length = str(len(self.playlist.track_list))
                self.playlist.clear()
                self.send_chat_msg('Deleted %s items in the playlist.' % pl_length)
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
                    self.send_chat_msg('Could not find anything matching: %s' % search_str)

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
                                track = self.playlist.add(self.active_user.nick, self.search_list[int_choice])
                                self.send_chat_msg('Added (%s) %s %s' %
                                                   (self.playlist.last_index,
                                                    track.title, self.format_time(track.time)))
                            else:
                                track = self.playlist.start(self.active_user.nick, self.search_list[int_choice])
                                self.send_yut_play(track.id, track.time, track.title)
                                self.timer(track.time)
                        else:
                            self.send_chat_msg('Please make a choice between 0-%s' % str(len(self.search_list) - 1))
                else:
                    self.send_chat_msg('No youtube track id\'s in the search list.')
            else:
                self.send_chat_msg('The search list only contains youtube playlist id\'s.')

    def do_clear(self):
        """ Clears the chat box. """
        self.send_chat_msg('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n Fobcity Bitch!'
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
 		    elif _user.user_level == 3 or _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
                        self.send_chat_msg('imma let ya guys figure that out...')
                    else:
                        self.send_kick_msg(_user.id)
 
    def do_forgive(self, nick_name):
        """
        Forgive a user based on if their user id (uid) is found in the room's ban list.
        :param nick_name: str the nick name of the user that was banned.
        """
        if self.is_client_mod:
            if len(nick_name) is 0:
                self.send_chat_msg(' Please state a nick to forgive from the ban list.')
	    else:
		    self.users.delete_banned_user(nick_name)
                    self.send_chat_msg('*' + nick_name + '* has been forgiven.')

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
		    elif _user.user_level == 3 or _user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:        
                        self.send_chat_msg('i dont wanna be a part of ya problems..')
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
            elif bad_nick in pinylib.CONFIG.B_NICK_BANS:
                self.send_chat_msg('%s is already in list.' % bad_nick)
            else:
                pinylib.file_handler.file_writer(self.config_path,
                                                 pinylib.CONFIG.B_NICK_BANS_FILE_NAME, bad_nick)

		if bots == 1 and bot_master == 1 or bots == 0: 
	                self.send_chat_msg('b1: %s added to banned nicks.' % bad_nick)
            	else: 
	                self.send_chat_msg('%s was added to banned nicks.' % bad_nick)
		self.load_list(nicks=True)

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
                if bad_nick in pinylib.CONFIG.B_NICK_BANS:
                    rem = pinylib.file_handler.remove_from_file(self.config_path,
                                                                pinylib.CONFIG.B_NICK_BANS_FILE_NAME,
                                                                bad_nick)
                    if rem:
			if bots == 1 and bot_master == 1 or bots == 0: 
	                	self.send_chat_msg('b2: %s removed from banned nicks.' % bad_nick)
            		else: 
	                	self.send_chat_msg('%s removed from banned nicks.' % bad_nick)

                        self.load_list(nicks=True)

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
                self.send_chat_msg('Ban string to short: ' + str(len(bad_string)))
            elif bad_string in pinylib.CONFIG.B_STRING_BANS:
                self.send_chat_msg('%s is already in list.' % bad_string)
            else:
                pinylib.file_handler.file_writer(self.config_path,
                                                 pinylib.CONFIG.B_STRING_BANS_FILE_NAME, bad_string)
		if bots == 1 and bot_master == 1 or bots == 0: 
     	          	self.send_chat_msg('b3: %s was added to banned words.' % bad_string)
		else:
                	self.send_chat_msg('%s was added to banned words.' % bad_string)
                self.load_list(strings=True)

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
                if bad_string in pinylib.CONFIG.B_STRING_BANS:
                    rem = pinylib.file_handler.remove_from_file(self.config_path,
                                                                pinylib.CONFIG.B_STRING_BANS_FILE_NAME,
                                                                bad_string)
                    if rem:
			if bots == 1 and bot_master == 1 or bots == 0: 
     	          		self.send_chat_msg('b4: %s was removed from banned words.' % bad_string)
			else:
                		self.send_chat_msg('%s was removed to banned words.' % bad_string)

                        self.load_list(strings=True)

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
                self.send_chat_msg('Account to short: ' + str(len(bad_account_name)))
            elif bad_account_name in pinylib.CONFIG.B_ACCOUNT_BANS:
                self.send_chat_msg('%s is already in list.' % bad_account_name)
            else:
                pinylib.file_handler.file_writer(self.config_path,
                                                 pinylib.CONFIG.B_ACCOUNT_BANS_FILE_NAME,
                                                 bad_account_name)
                if bots == 1 and bot_master == 1 or bots == 0: 
     	          	self.send_chat_msg('b5: %s was added to banned accounts.' % bad_account_name)
		else:
                	self.send_chat_msg('%s was added to banned accounts.' % bad_account_name)

		self.load_list(accounts=True)

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
                if bad_account in pinylib.CONFIG.B_ACCOUNT_BANS:
                    rem = pinylib.file_handler.remove_from_file(self.config_path,
                                                                pinylib.CONFIG.B_ACCOUNT_BANS_FILE_NAME,
                                                                bad_account)
                    if rem:

                	if bots == 1 and bot_master == 1 or bots == 0: 
     	          		self.send_chat_msg('b6: %s was removed from banned accounts.' % bad_account)
			else:
                		self.send_chat_msg('%s was removed from banned accounts.' % bad_account)
                        
			self.load_list(accounts=True)


    def do_verified(self, verified_name):

        if self.is_client_mod:
            if len(verified_name) is 0:
                self.send_chat_msg('Account can\'t be blank.')
            elif len(verified_name) < 3:
                self.send_chat_msg('Account too short: ' + str(len(verified_name)))
            elif verified_name in pinylib.CONFIG.B_ACCOUNT_VERIFIED:
                self.send_chat_msg('%s is already in list.' % verified_name)
            else:
                pinylib.file_handler.file_writer(self.config_path,
                                                 pinylib.CONFIG.B_ACCOUNT_VERIFIED_FILE_NAME,
                                                 verified_name)

		if bots == 1 and bot_master == 1 or bots == 0: 
     	        	self.send_chat_msg('b7: %s is verified now.' % verified_name)
		else:
			self.send_chat_msg('%s account is verified.' % verified_name)

                self.load_list(verified=True)

    def do_remove_verified(self, verified_account):
        if self.is_client_mod:
            if len(verified_account) is 0:
                self.send_chat_msg('Missing account.')
            else:
                if verified_account in pinylib.CONFIG.B_ACCOUNT_VERIFIED:
                    rem = pinylib.file_handler.remove_from_file(self.config_path,
                                                                pinylib.CONFIG.B_ACCOUNT_VERIFIED_FILE_NAME,
                                                                verified_account)
                    if rem:
			if bots == 1 and bot_master == 1 or bots == 0: 
     	        		self.send_chat_msg('b8: %s is not verified anymore.' % verified_account)
			else:
				self.send_chat_msg('Account %s was removed from verified accounts.' % verified_account)

                        self.load_list(verified=True)

    def do_chatmod(self, verified_name):

        if self.is_client_mod:
            if len(verified_name) is 0:
                self.send_chat_msg('Account can\'t be blank.')
            elif len(verified_name) < 3:
                self.send_chat_msg('Account too short: ' + str(len(verified_name)))
            elif verified_name in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
                self.send_chat_msg('%s is already in list.' % verified_name)
            else:
                pinylib.file_handler.file_writer(self.config_path,
                                                 pinylib.CONFIG.B_ACCOUNT_CHATMOD_FILE_NAME,
                                                 verified_name)
		if bots == 1 and bot_master == 1 or bots == 0: 
     	        	self.send_chat_msg('b9: %s is chat mod now.' % verified_name)
		else:
			self.send_chat_msg('%s is a chatmod now.' % verified_name)

	        self.load_list(chatmod=True)

    def do_remove_chatmod(self, verified_account):
        if self.is_client_mod:
            if len(verified_account) is 0:
                self.send_chat_msg('Missing account.')
            else:
                if verified_account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
                    rem = pinylib.file_handler.remove_from_file(self.config_path,
                                                                pinylib.CONFIG.B_ACCOUNT_CHATMOD_FILE_NAME,
                                                                verified_account)
                    if rem:
			if bots == 1 and bot_master == 1 or bots == 0: 
     	        		self.send_chat_msg('b0: %s was removed as a chat mod.' % verified_account)
			else:
				self.send_chat_msg('%s is not a chatmod anymore.' % verified_account)

                        self.load_list(chatmod=True)

    def do_user_info(self, user_name):
        """ 
        Shows user object info for a given user name.

        :param user_name: The user name of the user to show the info for.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.send_chat_msg('Missing username.')
            else:
                _user = self.users.search_by_nick(user_name)
                if _user is None:
                    self.send_chat_msg('No user named: %s' % user_name)
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

                    self.send_chat_msg('\n'.join(info))

    def do_cam_approve(self, user_name):
        """
        Allow a user to broadcast in a green room enabled room.

        :param user_name:  The name of the user allowed to broadcast.
        :type user_name: str
        """
        _user = self.users.search_by_nick(user_name)
        if len(user_name) > 0:
                if _user is not None and _user.is_waiting:
                    self.send_cam_approve_msg(_user.id)
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
                self.send_private_msg(self.active_user.nick, 'No track playing.')

    def do_who_plays(self):
        """ Show who requested the currently playing track. """
        if self.is_client_mod:
            if self.playlist.has_active_track:
                track = self.playlist.track
                ago = self.format_time(int(pinylib.time.time() - track.rq_time))
                self.send_chat_msg('%s requested this track %s ago.' % (track.owner, ago))
            else:
                self.send_chat_msg('No track playing.')

    def do_help(self):
        """ Posts a link to github readme/wiki or other page about the bot commands. """
		    
	if self.active_user.user_level < 5 or self.active_user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
		time.sleep(1)
		self.send_private_msg(self.active_user.id, 'Mod Cmds: !clr, !kick, !ban, !cam, !close, !bada  <account>, !banw <badword>,!rmw <badword>, !rmbad <account>, !badn <nick>')
	if self.active_user.user_level < 5 or self.active_user.account in pinylib.CONFIG.B_ACCOUNT_VERIFIED:
		time.sleep(4)
		self.send_private_msg(self.active_user.id, 'Media Cmds: !yt, !close, !seek, !reset, !spl, !del, !skip, !yts, !rpl, !pause, !play, !pyst')
	if self.active_user.user_level == 3 or self.active_user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
	        chatmod = ''
		if self.active_user.user_level == 3:
			chatmod = '!chatmod <account>, !rmchatmod,'
		time.sleep(1)
		self.send_private_msg(self.active_user.id, 'Admin Cmds: !lockdown (noguests), !lockup(password enabled), !demod, !v <account>, !rmv,'+chatmod+', !noguest')

    def do_play_youtube(self, search_str):
        """ 
        Plays a youtube video matching the search term.

        :param search_str: The search term.
        :type search_str: str
        """
        log.info('user: %s:%s is searching youtube: %s' % (self.active_user.nick, self.active_user.id, search_str))
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
                        track = self.playlist.add(self.active_user.nick, _youtube)
                        self.send_chat_msg('(%s) %s %s' %
                                           (self.playlist.last_index, track.title, self.format_time(track.time)))
                    else:
                        track = self.playlist.start(self.active_user.nick, _youtube)
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

        if self.has_level(1):
            if self.is_client_owner:
                pass

	    elif pm_cmd == prefix + 'help':
                self.do_help()
            elif pm_cmd == prefix + 'clrbn':
                self.do_clear_bad_nicks()

            elif pm_cmd == prefix + 'clrbs':
                self.do_clear_bad_strings()

            elif pm_cmd == prefix + 'clrba':
                self.do_clear_bad_accounts()

        self.console_write(pinylib.COLOR['white'], 'Private message from %s: %s' % (self.active_user.nick, private_msg))

    def on_quitting(self, uid, account):

        if account in botnet:
             botnet.remove(account)
             self.console_write(pinylib.COLOR['bright_yellow'], 'Bot: %s unregistered.' % (account))
             del botnet[:]
             bots = False

    def do_clear_bad_nicks(self):
        """ Clear the nick bans file. """
        pinylib.CONFIG.B_NICK_BANS[:] = []
        pinylib.file_handler.delete_file_content(self.config_path, pinylib.CONFIG.B_NICK_BANS_FILE_NAME)

    def do_clear_bad_strings(self):
        """ Clear the string bans file. """
        pinylib.CONFIG.B_STRING_BANS[:] = []
        pinylib.file_handler.delete_file_content(self.config_path, pinylib.CONFIG.B_STRING_BANS_FILE_NAME)

    def do_clear_bad_accounts(self):
        """ Clear the account bans file. """
        pinylib.CONFIG.B_ACCOUNT_BANS[:] = []
        pinylib.file_handler.delete_file_content(self.config_path, pinylib.CONFIG.B_ACCOUNT_BANS_FILE_NAME)

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
        log.info('options: is_client_owner: %s, is_client_mod: %s' % (self.is_client_owner, self.is_client_mod))

        if self.is_client_mod:
        	self.send_banlist_msg()

        self.load_list(nicks=True, accounts=True, strings=True, verified=True, chatmod=True)
	
	who_am_i = '['+str(self.account)+']'
        h = MD5.new()
        h.update(who_am_i)
         
	global bot_id

        bot_id = h.hexdigest()
	self.send_chat_msg('YABUDDY - '+str(bot_id))

    def load_list(self, nicks=False, accounts=False, strings=False, verified=False, chatmod=False):
        """
        Loads different list to memory.
        
        :param nicks: bool, True load nick bans file.
        :param accounts: bool, True load account bans file.
        :param strings: bool, True load ban strings file.
        """
        if nicks:
            pinylib.CONFIG.B_NICK_BANS = pinylib.file_handler.file_reader(self.config_path,
                                                                          pinylib.CONFIG.B_NICK_BANS_FILE_NAME)
        if accounts:
            pinylib.CONFIG.B_ACCOUNT_BANS = pinylib.file_handler.file_reader(self.config_path,
                                                                             pinylib.CONFIG.B_ACCOUNT_BANS_FILE_NAME)
        if verified:
            pinylib.CONFIG.B_ACCOUNT_VERIFIED = pinylib.file_handler.file_reader(self.config_path,
                                                                             pinylib.CONFIG.B_ACCOUNT_VERIFIED_FILE_NAME)
        if chatmod:
            pinylib.CONFIG.B_ACCOUNT_CHATMOD = pinylib.file_handler.file_reader(self.config_path,
                                                                             pinylib.CONFIG.B_ACCOUNT_CHATMOD_FILE_NAME)
        if strings:
            pinylib.CONFIG.B_STRING_BANS = pinylib.file_handler.file_reader(self.config_path,
                                                                            pinylib.CONFIG.B_STRING_BANS_FILE_NAME)

    def has_level(self, level):
        """ 
        Checks the active user for correct user level.

        :param level: The level to check the active user against.
        :type level: int
        :return: True if the user has correct level, else False
        :rtype: bool
        """
        if self.active_user.user_level == 6:
            return False
        elif self.active_user.user_level <= level:
            return True
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
        for bad in pinylib.CONFIG.B_STRING_BANS:
            if bad.startswith('*'):
                _ = bad.replace('*', '')
                if _ in msg:
                    should_be_banned = True
            elif bad in chat_words:
                    should_be_banned = True

	if bots == 1 and bot_master == 1 or bots == 0: 

		if len(self.active_user.account) is 0 or len(self.active_user.account) is not 0 and self.active_user.account not in pinylib.CONFIG.B_ACCOUNT_VERIFIED or len(self.active_user.account) is not 0 and self.active_user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
	
			if len(lastmsgs) is 0:
				lastmsgs.append(msg)
				self.console_write(pinylib.COLOR['bright_yellow'], 'Spam: Protection on.')

			else:	
				msg_count = str(len(lastmsgs))
				self.console_write(pinylib.COLOR['bright_yellow'], 'Spam: Processing - %s' % (msg_count))

				if msg in lastmsgs:
					spam += 1
					lastmsgs.append(msg)
					spammer = self.active_user.nick
					self.console_write(pinylib.COLOR['bright_yellow'], 'Spam: Found Spammer %s' % (self.active_user.nick))
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
				self.console_write(pinylib.COLOR['bright_yellow'], 'Spam: Resetting last message db.')

	if should_be_banned:
			if self.active_user.account in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
				pass	
			elif self.active_user.account in pinylib.CONFIG.B_ACCOUNT_VERIFIED and self.active_user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD: 
				pass
			elif len(self.active_user.account) is not 0 and self.active_user.account not in pinylib.CONFIG.B_ACCOUNT_VERIFIED or len(self.active_user.account) is not 0 and self.active_user.account not in pinylib.CONFIG.B_ACCOUNT_CHATMOD:
				if is_a_spammer: 
		 			self.do_bad_account(self.active_user.account)
					is_a_spammer = False
				if bots == 1 and bot_master == 1 or bots == 0: 
					self.do_clear()
				self.send_ban_msg(self.active_user.id)
		     	elif len(self.active_user.account) is 0:
				if is_a_spammer: 
					is_a_spammer = False
				if bots == 1 and bot_master == 0 or bots == 0: 
					self.do_clear()
				self.send_ban_msg(self.active_user.id)

			self.console_write(pinylib.COLOR['cyan'], 'Spam: Flood, Repeat or Badword by %s' % (self.active_user.nickt))

    def check_lockstatus(self, msg):
           
            global bots
	    global bot_id
            global bot_master
            global botnet

            chat_words = msg.split(' ')
     
            LOCKDOWN_KEYWORDS = ("a0:",)
            REOPEN_KEYWORDS = ("a1:",)
            AUTH_KEYWORDS = ("YABUDDY","ohhai","ehyo","ehyo","ehy",)
            UPDATE_KEYWORDS = ("b0:","b1:","b2:","b3:","b4:","b5:","b6:","b7:","b8:","b9:",)

            for word in chat_words:
                if word in AUTH_KEYWORDS:

		    self.console_write(pinylib.COLOR['bright_yellow'], 'Bot: Auth request: %s' % (self.active_user.nick))
                    if self.active_user.account != self.account and self.active_user.user_level == 3 or self.active_user.user_level == 1:

                        who_is = '['+str(self.active_user.account)+']'
                        b = MD5.new()
                        b.update(who_is)
                        auth_botid = b.hexdigest()
                        auth_botid = str(auth_botid)
                        thisphase = word
                        next_authkey = chat_words[chat_words.index(thisphase)+2]
		        
                        if next_authkey == auth_botid:
                            if self.active_user.account in botnet:
				pass
                            else:
				botnet.append(self.active_user.account)
                                self.console_write(pinylib.COLOR['bright_yellow'], 'Bot: %s registered.' % (self.active_user.nick))
                                bots = True 
				if word == "ehyo":
					pass
				else:
					time.sleep(3)
                                	self.send_chat_msg('ehyo %s! %s' % (self.active_user.nick, bot_id))

                if word.lower() in LOCKDOWN_KEYWORDS:
                    if self.active_user.account != self.account and self.active_user.user_level == 3 or self.active_user.user_level == 1:
                        if self.active_user.account in botnet:
			    lockdown = True
                            self.console_write(pinylib.COLOR['bright_yellow'], 'Lockdown started by %s' % (self.active_user.nick))
                        else:
                            self.send_chat_msg('hmm, should i do something?')

                if word.lower() in REOPEN_KEYWORDS:
                    if self.active_user.account != self.account and self.active_user.user_level == 3 or self.active_user.user_level == 1:
                        if self.active_user.account in botnet:
			    lockdown = False
                            self.console_write(pinylib.COLOR['bright_yellow'], 'Lockdown reset by %s' % (self.active_user.nick))  
                        else:
                            self.send_chat_msg('its over but i am not sure')

                if word.lower() in UPDATE_KEYWORDS:
                    if self.active_user.account != self.account and self.active_user.user_level == 3 or self.active_user.user_level == 1:
                        if self.active_user.account in botnet:
	                        thisphase = word
	                        whatwhat = chat_words[chat_words.index(thisphase)+1]
	
				if word == "b1:":
					self.do_bad_nick(whatwhat)
	                        	#self.send_chat_msg('that nick sucks anyhow...')
				if word == "b2:":
					self.do_remove_bad_nick(whatwhat)
				        #self.send_chat_msg('friends...')
				if word == "b3:":
					self.do_bad_string(whatwhat)
					#self.send_chat_msg('police state shit...')
				if word == "b4:":
					self.do_remove_bad_string(whatwhat)
					#self.send_chat_msg('freedom of speech!')
				if word == "b5:":
					self.do_bad_account(whatwhat)
					#self.send_chat_msg('lol!')
				if word == "b6:":
					self.do_remove_bad_account(whatwhat)
					#self.send_chat_msg('lets be friends!')
				if word == "b7:":
					self.do_verified(whatwhat)			
					#self.send_chat_msg('yes! cam the eff up')
				if word == "b8:":
					self.do_remove_verified(whatwhat)			
					#self.send_chat_msg('you be a nobody again')
				if word == "b9:":
					self.do_chatmod(whatwhat)		
					#self.send_chat_msg('your wish is my command')
				if word == "b0:":
					self.do_remove_chatmod(whatwhat)			
					#self.send_chat_msg('we couldve been somebody')
