# -*- coding: utf-8 -*-
""" Tinybot by Nortxort (https://github.com/nortxort/tinybot-rtc) """
""" Modified by odsum (https://github.com/odsum/buddytinychatbot) """

import time
import threading
import config
from page import privacy, acc
import socket
import base64

__version__ = '1.1 - Buddy HUB'

class TinychatBot():
    privacy_ = None
    global key
    key = config.KEY

    def decode(self, enc):
        dec = []
        enc = base64.urlsafe_b64decode(enc)
        for i in range(len(enc)):
                key_c = key[i % len(key)]
                dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
                dec.append(dec_c)
        return "".join(dec)

    def listen(self):
	print('Hub started')
  	self.host = socket.gethostname()
        self.port = config.HUB_PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
	self.sock.listen(2)
	while True:
            client, address = self.sock.accept()
            client.settimeout(60)
            threading.Thread(target = self.listenToClient,args = (client,address)).start() 

    def listenToClient(self, client, address):
        size = 1024
        while True:
            try:
                data = client.recv(size)
	        print('Connection from: %s' % (str(address)))

                if data:
				print('Raw Data %s' % (str(data)))
				data = self.decode(data)
				data = data.split(':')	
			
				if "hellomonkey" in data:
					a = self.do_lockdown(data[1])
					a = str(a) 
					client.send(a)
					acc.Account.logout() #log account off its on
			        	print('Hub: logged out from Tinychat.')
			        	print('Lockdown request complete')

				if  "donkeykong" in data:
					b = do_push2talk()
			        	b = str(b)
					client.send(b)
			        	print('P2T requst from: %s' % (str(address)))
					acc.Account.logout() #log account off its on
			        	print('P2T request complete')

 				else:
                    			raise error('Client disconnected')

            except:
                client.close()
                return False

    def do_lockdown(self, password):
	    print('Lockdown request')
	    account = acc.Account(account=config.ACCOUNT, password=config.PASSWORD)
	    account.login()
	    print('Hub: Logged into Tinychat.')

            privacy_ = privacy.Privacy(proxy=None)
            privacy_.parse_privacy_settings()
	    
            if not privacy_.set_guest_mode():
		if password != 'None':
			privacy_.set_room_password(password)
			print('Lockdown password: %s' % (password))
		else:
			print('Lockdown no guest mode')

		return 0 
            else:
		password = None
		privacy_.set_room_password(password)
	        print('Hub: Room open to the public again')
		return 1
	
    def do_make_mod(self, account):

                tc_user = self.privacy_.make_moderator(account)
                if tc_user is None:
                    self.send_chat_msg('The account is invalid.')
                elif not tc_user:
		    pass
                elif tc_user:
                    self.send_chat_msg('%s was made a room moderator.' % account)

    def do_remove_mod(self, account):

                tc_user = self.privacy_.remove_moderator(account)
                if tc_user:
                    self.send_chat_msg('%s is no longer a room moderator.' % account)
                elif not tc_user:
                    self.send_chat_msg('%s is not a room moderator.' % account)

    def do_directory(self):
            if self.privacy_.show_on_directory():

                self.send_chat_msg('Room IS shown on the directory.')
            else:
                self.send_chat_msg('Room is NOT shown on the directory.')

    def do_push2talk(self):
	    self.get_privacy_settings()
            if self.privacy_.set_push2talk():
		return 0
            else:
		return 1
		
    def do_green_room(self):
            if self.privacy_.set_greenroom():
                self.send_chat_msg('Green room is enabled.')
            else:
                self.send_chat_msg('Green room is disabled.')

    def do_clear_room_bans(self):
            if self.privacy_.clear_bans():
                self.send_chat_msg('All room bans was cleared.')

    def do_room_settings(self):
            settings = self.privacy_.current_settings()
            self.send_chat_msg(
                'Broadcast Password: ' + settings['broadcast_pass'] + '\n' +
                'Room Password: ' + settings['room_pass'] + '\n' +
                'Login Type: ' + settings['allow_guest'] + '\n' +
                'Directory: ' + settings['show_on_directory'] + '\n' +
                'Push2Talk: ' + settings['push2talk'] + '\n' +
                'Greenroom: ' + settings['greenroom']
            )

	

