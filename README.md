
## BuddyBot

Based off Nortxort's Tinychat Bot and Pinylib.

## Updates
2.2.4
- Clean up tinyboy.py, finally using pyCharm
- Resorted Pinylib.py and user.py back to default
- Fixed pickble.py dexists issue with Nortxort's suggestion
- Added in the concept and idea for multiple bots to bot.py

2.2.2
- Announcements:  Update your config.py to include B_ANNOUNCEMENT, to set temporary announcements use !announcement <msg>
- Moved all cmds to handled at one place, bot responses mostly in private messages now
- Nortxort fixes to loading database
- Added back in APIs: weather, 8ball, etc.

2.2
- Added in new wrapper class written by Nortxort
	- Old database files not used, you could write a merge script to import that list to new one
- Spam messaging re-written (Need testing)
	- Scoring system to validate messags

## Features

- Spam Protection
	- On Join flooding
	- Spam Repeat text
	- Spam Score System
	- Random nick Check
	- Lockdown with password or no guest mode (Owner mode)

- User System
	- Verified Accounts can control youtube and auto-cam'ed by bot
	- !v <account> - verified accounts 
	- !chatmod <account> - chatmod
	- !chatadmin <account> - chatadmin - control lockdown, add real mods, and other room settings

	7 - guest
	6 - has account not verified
	5 - verified user
	4 - Chatmod
	3 - Regular Mod
	2 - Chatadmin
	1 - Owner/Bot

- Dj Mode
	- Limits all chatmods and Verified Accounts from using youtube unless a dj is defined.
	- !djmode and !dj <nick>

## Road Map

3.0 
- Sqlite for database
- Web interface to Manage Accounts, bot settings
- Mulitple rooms where the bot can be to manage
 
2.5 
- Custom greeting messages per accounts
- Vote Ban System
- Clean up forgive, maybe bring in one from Nortxort's TinychatBot
- Mutliple bots in various rooms

## Commands

	Verified Accounts:
	Media Cmds: !yt, !close, !seek, !reset, !spl, !del, !skip, !yts, !rpl, !pause, !play, !pyst

	Chatmods and !mod tmp users:
	Mod Cmds: !clr, !kick, !ban, !cam, !close, !bada  <account>, !banw <badword>,!rmw <badword>, !rmbad <account>, !badn <nick>, !chatmod, !v, !rmv, !dechatmod

	Mods and Admins:
	Admin Cmds: !lockdown (noguests), !lockup(password enabled), !noguest, !p2t

	Other cmds: !urb, !8ball, !flip, !roll, !whoplayed, !now, !status, !chuck, !wea


## Pinylib-RTC

WebRTC module for tinychat chat rooms.

This is the WebRTC version of pinylib. The structure and the coding style is the same as the original pinylib. Since tinychat is still in beta stage, this version should also be seen as a sort of beta version.

It was based on the [POC](https://github.com/notnola/TcRTC) by [notnola](https://github.com/notnola)


## Setting up

Examples shown here, assumes you are using windows.

pinylib-rtc was developed using [python 2.7.10](https://www.python.org/downloads/windows/ "python for windows") so this is the recomended python interpreter. Later versions of python should work to, aslong as they are from the 2.7 family. I have not tested it with python 3, but with a few changes to client.py i think it would be possible.

### Requirements

pinylib-rtc requires 4 libraries that are not part of the standard python library, these being:

* [websocket-client](https://github.com/websocket-client/websocket-client)
* [requests](https://github.com/kennethreitz/requests "requests")
* [colorama](https://github.com/tartley/colorama "Colorama")
* [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/ "beautifulsoup4")

These can all be installed form a command prompt with pip.

`pip install websocket-client requests colorama beautifulsoup4`


## Run the client

Run the client by typing `python path\to\bot.py` in a command prompt.


## Authors
* [odsum](https://github.com/odsum)
* [nortxort](https://github.com/nortxort)


## License

The MIT License (MIT)

Copyright (c) 2018 Notnola
Copyright (c) 2018 Nortxort
Copyright (c) 2018 Odsum

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

