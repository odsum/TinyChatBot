
## Buddy Modified Tinychat Bot

Based off Nortxort's Tinychat Bot and Pinylib.
For further questions, catch me online as buddy in http://tinychat.com/fobcity
BTW: I am not a programmer, I learnt Python a few weeks ago.
Account Management is done via users.db, might have to create it by hand first.  {users:{}}

- Spam Protection
	- On Join flooding
	- Spam Repeat text
	- Hub communication to lockdown the room with a randomized Password

- Verification System
	- Verified Accounts can control youtube and auto-cam'ed by bot

- Dj Mode
	- Limits all chatmods and Verified Accounts from using youtube unless a dj is defined.
	- !djmode and !dj <nick>

- Chat Mods
	- Chat moderations can !kick and !ban, other mod cmds

- Hub System
	- Keep the main room account offline and communicates lockdown and lockup, push to talk
	
	To enable:
	B_BOT_HUB = True
	B_BOT_HUB_HOST = ''
	B_BOT_HUB_PORT = 1337
	B_HUB_KEY = '12345678' 
	
	run /hub/bot.py

- Dual Bot System, basic zero-configuration approach
	- If more than one bot, the functionality for media is given to the not Master bot
		
	B_BOT_MASTER = True  # if defined, this bot will not do the media functions if there is another bot online.


- Things to do
	- Chat log analytics
	- Hub system to include add and remove Moderators 
	- Administrator user level which allow admin defined users to access Add/Remove Monderators
	- unban, !forgive is not working
	- Clean up code, move on_join checking to another function
	- Vote Banning System
	- Update to python 3

- Commands:

	Verified Accounts:
	Media Cmds: !yt, !close, !seek, !reset, !spl, !del, !skip, !yts, !rpl, !pause, !play, !pyst

	Chatmods and !mod tmp users:
	Mod Cmds: !clr, !kick, !ban, !cam, !close, !bada  <account>, !banw <badword>,!rmw <badword>, !rmbad <account>, !badn <nick>, !chatmod, !v, !rmv, !dechatmod

	Mods and Admins:
	Admin Cmds: !lockdown (noguests), !lockup(password enabled), !noguest, !p2t

	Other cmds: !urb, !8ball, !flip, !roll, !whoplayed, !now, !status, !chuck, !wea

Run gib_detect_train.py first to generate a db.


## Pinylib-RTC

WebRTC module for tinychat chat rooms.

This is the WebRTC version of pinylib. The structure and the coding style is the same as the original pinylib. Since tinychat is still in beta stage, this version should also be seen as a sort of beta version.

It was based on the [POC](https://github.com/notnola/TcRTC) by [notnola](https://github.com/notnola)


## Setting up

Examples shown here, assumes you are using windows.

pinylib-rtc was developed using [python 2.7.10](https://www.python.org/downloads/windows/ "python for windows") so this is the recomended python interpreter. Later versions of python should work to, aslong as they are from the 2.7 family. I have not tested it with python 3, but with a few changes to client.py i think it would be possible.

### Requirements

pinylib-rtc requires 4 libraries that are not part of the standard python library, these being:

* https://pypi.python.org/pypi/pycrypto
* [websocket-client](https://github.com/websocket-client/websocket-client)
* [requests](https://github.com/kennethreitz/requests "requests")
* [colorama](https://github.com/tartley/colorama "Colorama")
* [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/ "beautifulsoup4")

These can all be installed form a command prompt with pip.

`pip install websocket-client requests colorama beautifulsoup4 pycryto`


## Run the client

Run the client by typing `python path\to\bot.py` in a command prompt.

!v <account> to verify
!chatmod <account> to add as a chatmod


## Authors
* [odsum] (https://github.com/odsum)
* [nortxort](https://github.com/nortxort)


## License

The MIT License (MIT)

Copyright (c) 2017 Notnola

Copyright (c) 2017 Nortxort

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice
shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Acknowledgments
*Thanks to the following people who in some way or another, has helped with this project*

* [notnola](https://github.com/notnola)


