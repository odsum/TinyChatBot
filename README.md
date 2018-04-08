
## BuddyBot

Based off Nortxort's Tinychat Bot and Pinylib.

### Updates

### 2.4.5
- Spam protection updates - bugs fixed, tested.

2.4
- !camban - ban nicks from camming up
- Fixed spam protection, holds against spam bots now
- fixed other bugs related to global vars talking between modules
- added welcome, register as modules of their own


2.3.2 
- !verobose - to enable or disable the bot from showing respones for cmds in chat
- !allowcam - No one is allowed to cam up
- !acc - New account manager
    - !acc camban account reason for cambans
- !tokes/!cheers mins - Countdown, !tokes or !cheers to join in
- !vote - !voteban cam/ban account, !vote for yes if there is 5 votes.
    - cam will close cam
    - ban will ban the user
 
- !vip - Allow only users with accounts in bot to join the room
- Custom Users welcome messages, !acc add account verified Welcome Message

2.2.9
- Multiple Room Support
    - config.py ROOMS=['room1','room2','etc']

- Spam Protection updates based on testing
- Bot reconnect to TinyChat after disconnect
- Spam: Kick/ban flood pool for lockdown mode so bot doesn't flood out 


### Features

- Spam Protection
    - Enable and disable Spam protection
    -       !spam
	- On Join flooding
	- Spam Repeat text
	- Spam Score System
	- Random nick Check
	- Lockdown with password or no guest mode (Owner mode)

- User System
	- Verified Accounts can control youtube and auto-cam'ed by bot
	- !acc account level welcomemessage/reason
    -       !acc add odsum mod/admin/verified my welcome greeting
    -       !acc del odsum 
    -       !acc camban odsum smokes on cam
    -       !acc ban odsum reason of ban

    #### Account levels
    9 - Banned account<br />
    8 - Camban<br />
    7 - guest<br />
    6 - has account not verified<br />
    5 - verified/whitelist user<br />
    4 - Chatmod<br />
    3 - Regular Mod<br />
    2 - Chatadmin<br />

- Dj Mode
	- Limits all chatmods and Verified Accounts from using youtube unless a dj is defined.
	- !djmode and !dj <nick>

## Road Map

3.0 
- Sqlite for database
- Web interface to Manage Accounts, bot settings
 
## Commands

	Verified Accounts:
	Media Cmds: !yt, !close, !seek, !reset, !spl, !del, !skip, !yts, !rpl, !pause, !play, !pyst

	Chatmods and !mod tmp users:
	Mod Cmds: !clr, !camban, !kick, !ban, !cam, !close, !banw <badword>,!rmw <badword>, !badn <nick>, !acc, !+tmod, !-tmod, !verobose, !allowcam, !spam, !vote

	Mods and Admins:
	Admin Cmds: !lockdown (noguests), !lockup(password enabled), !noguest, !p2t, !+mod, !-mod

	Other cmds: !urb, !8ball, !flip, !roll, !whoplayed, !now, !status, !chuck, !wea, !cheers, !tokes

    Account Management:
        !acc add odsum mod/admin/verified my welcome greeting
        !acc del odsum 
        !acc camban odsum smokes on cam
        !acc ban odsum reason of ban

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

`pip install websocket-client requests colorama beautifulsoup4 simplejson`


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

