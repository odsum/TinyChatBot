from bs4 import BeautifulSoup
import util.web


class Privacy:
    """
    This class represents tinychat's privacy page for a room,
    it contains methods to change a rooms privacy settings.
    """

    def __init__(self, proxy):
        """ Create a instance of the Privacy class.

        :param proxy: A proxy in the format IP:PORT
        :type proxy: str | None
        """
        self._proxy = proxy
        self._privacy_url = 'https://tinychat.com/settings/privacy'
        self._csrf_token = ''
        self._room_password = None
        self._roompass_enabled = 0
        self._broadcast_password = None
        self._broadcast_pass_enabled = 0
        self.room_moderators = list()
        self._form_data = dict()

    @staticmethod
    def _is_tc_account(account_name):
        """ Helper method to check if a user account is a valid account name.

        :param account_name: The account name to check.
        :type account_name: str
        :return: True if it is a valid account, False if invalid account.
        :rtype: bool
        """
        url = 'https://tinychat.com/api/tcinfo?username=%s' % account_name
        response = util.web.http_get(url=url, json=True)
        if response['json'] is not None:
            if 'error' not in response['json']:
                return True
            return False

    def clear_bans(self):
        """ Clear all room bans.

        :return: True if bans were cleared, else False.
        :rtype: bool
        """
        url = 'https://tinychat.com/settings/privacy/clearbans'
        header = {
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': self._privacy_url
        }
        form_data = {'_token': self._csrf_token}
        response = util.web.http_post(post_url=url, post_data=form_data, header=header,
                                      json=True, proxy=self._proxy)
        if response['json']['error'] is False:
            if response['json']['response'] == 'Bans cleared':
                return True
        return False

    def parse_privacy_settings(self, response=None):
        """ Parse privacy settings.

        :param response: A http response.
        :type response: dict
        """
        if response is None:
            response = util.web.http_get(url=self._privacy_url, referer=self._privacy_url, proxy=self._proxy)

        if response is not None and response['content'] is not None:
            soup = BeautifulSoup(response['content'], 'html.parser')
            # csrf-token
            token = soup.find(attrs={'name': 'csrf-token'})
            self._csrf_token = token['content']
            # guest settings
            guest_settings = soup.find('input', {'name': 'allow_guest', 'checked': True})
            if guest_settings is not None:
                self._form_data['allow_guest'] = 1
                twitter = soup.find('input', {'name': 'require_twitter', 'checked': True})
                if twitter is not None:
                    self._form_data['require_twitter'] = 1
                else:
                    self._form_data['require_twitter'] = 0
                facebook = soup.find('input', {'name': 'require_facebook', 'checked': True})
                if facebook is not None:
                    self._form_data['require_facebook'] = 1
                else:
                    self._form_data['require_facebook'] = 0
            else:
                self._form_data['allow_guest'] = 0
                self._form_data['require_twitter'] = 0
                self._form_data['require_facebook'] = 0
            # directory setting
            dir_settings = soup.find('input', {'name': 'public_directory', 'checked': True})
            if dir_settings is not None:
                self._form_data['public_directory'] = 1
            else:
                self._form_data['public_directory'] = 0
            # push2talk setting
            push2talk = soup.find('input', {'name': 'push2talk', 'checked': True})
            if push2talk is not None:
                self._form_data['push2talk'] = 1
            else:
                self._form_data['push2talk'] = 0
            # greenroom setting
            greenroom = soup.find('input', {'name': 'greenroom', 'checked': True})
            if greenroom is not None:
                self._form_data['greenroom'] = 1
            else:
                self._form_data['greenroom'] = 0
            # room password
            roompass = soup.find(attrs={'name': 'roomPassword'})
            if roompass['value']:
                self._roompass_enabled = 1
            else:
                self._roompass_enabled = 0
            # TODO:make sure this works as expected
            if not self._form_data['greenroom']:
                # broadcast password
                broadcast_pass = soup.find(attrs={'name': 'broadcastPassword'})
                if broadcast_pass['value']:
                    self._broadcast_pass_enabled = 1
                else:
                    self._broadcast_pass_enabled = 0
            # moderators
            # There has to be a more elegant way of doing this..
            pattern = 'var moderators = \''
            if pattern in response['content']:
                mod_str = str(response['content']).split(pattern)[1].split('\';')[0].replace('"', '\'')
                mod_str_replaced = mod_str.replace('[', '').replace(']', '').replace('\'', '')
                mods = mod_str_replaced.split(',')
                if len(mods) > 0:
                    for mod in mods:
                        if mod != '' and mod not in self.room_moderators:
                            self.room_moderators.append(mod)

    def set_room_password(self, password=None):
        """ Set a room password or clear the password.

        :param password: The room password or None to clear.
        :type password: str | None
        """
        if password is None:
            self._room_password = ''
        else:
            self._room_password = password
        if self._broadcast_password is None:
            self._broadcast_password = ''

        form_data = {
            'roomPassword': self._room_password,
            'broadcastPassword': self._broadcast_password,
            'privacy_password': 1,
            '_token': self._csrf_token
        }
        res = util.web.http_post(post_url=self._privacy_url, post_data=form_data,
                                 referer=self._privacy_url, follow_redirect=True)
        self.parse_privacy_settings(response=res)

    def set_broadcast_password(self, password=None):
        """ Set a broadcast password or clear the password.

        :param password: The broadcast password or None to clear.
        :type password: str | None
        """
        if password is None:
            self._broadcast_password = ''
        else:
            self._broadcast_password = password
        if self._room_password is None:
            self._room_password = ''

        form_data = {
            'roomPassword': self._room_password,
            'broadcastPassword': self._broadcast_password,
            'privacy_password': 1,
            '_token': self._csrf_token
        }
        res = util.web.http_post(post_url=self._privacy_url, post_data=form_data,
                                 referer=self._privacy_url, follow_redirect=True)
        self.parse_privacy_settings(response=res)

    def make_moderator(self, account):
        """ Make a user account a moderator.

        :param account: The account to make a moderator.
        :type account: str
        :return True if the account was added as a moderator, False if already a moderator
        or None on invalid account name.
        :rtype: bool | None
        """
        url = 'https://tinychat.com/settings/privacy/addfeatureduser'
        if self._is_tc_account(account):
            if account not in self.room_moderators:
                form_data = {
                    '_token': self._csrf_token,
                    'name': account,
                    'type': 'moderator'
                }
                response = util.web.http_post(post_url=url, post_data=form_data, json=True, proxy=self._proxy)
                if response['json']['error'] is False and response['json']['response'] == 'Data added':
                    self.parse_privacy_settings()
                    if account in self.room_moderators:
                        return True
                return False
            return False
        return None

    def remove_moderator(self, account):
        """ Remove a room moderator.

        :param account: The moderator account to remove.
        :return: True if removed else False
        :rtype: bool
        """
        url = 'https://tinychat.com/settings/privacy/removefeatureduser'
        if account in self.room_moderators:
            form_data = {
                '_token': self._csrf_token,
                'name': account,
                'type': 'moderator'
            }
            response = util.web.http_post(post_url=url, post_data=form_data, json=True, proxy=self._proxy)
            if response['json']['error'] is False and response['json']['response'] == 'Data removed':
                self.room_moderators.remove(account)
                return True
            return False
        return False

    def set_guest_mode(self):
        """ Enable/disable guest mode.

        NOTE: I don't know if it is a bug on tinychat's end, but whether this is set or not,
        does not seem to matter, you can still join as guest.

        :return: True if guests are allowed, else False.
        :rtype: bool
        """
        if not self._form_data['allow_guest']:
            self._form_data['allow_guest'] = 1
            self._update()
            return True
        elif self._form_data['allow_guest']:
            self._form_data['allow_guest'] = 0
            self._form_data['require_twitter'] = 0
            self._form_data['require_facebook'] = 0
            self._update()
            return False

    def set_guest_mode_twitter(self):
        """ Enable/disable guest mode twitter.

        :return: True if guest mode is set to twitter, else False.
        :rtype: bool
        """
        if self._form_data['allow_guest']:
            if not self._form_data['require_twitter']:
                self._form_data['require_twitter'] = 1
                self._update()
                return True
            elif self._form_data['require_twitter']:
                self._form_data['require_twitter'] = 0
                self._update()
                return False
        else:
            self._form_data['allow_guest'] = 1
            self._form_data['require_twitter'] = 1
            self._update()
            return True

    def set_guest_mode_facebook(self):
        """ Enable/disable guest mode facebook.

        :return: True if guest mode is set to facebook, else False.
        :rtype: bool
        """
        if self._form_data['allow_guest']:
            if not self._form_data['require_facebook']:
                self._form_data['require_facebook'] = 1
                self._update()
                return True
            elif self._form_data['require_facebook']:
                self._form_data['require_facebook'] = 0
                self._update()
                return False
        else:
            self._form_data['allow_guest'] = 1
            self._form_data['require_facebook'] = 1
            self._update()
            return True

    def show_on_directory(self):
        """ Enables/disables show up on directory setting.

        :return: True if enabled else False.
        :rtype: bool
        """
        if not self._form_data['public_directory']:
            self._form_data['public_directory'] = 1
            self._update()
            return True
        elif self._form_data['public_directory']:
            self._form_data['public_directory'] = 0
            self._update()
            return False

    def set_push2talk(self):
        """ Enables/disables push2talk setting.

        :return: True if enabled else False.
        :rtype: bool
        """
        if not self._form_data['push2talk']:
            self._form_data['push2talk'] = 1
            self._update()
            return True
        elif self._form_data['push2talk']:
            self._form_data['push2talk'] = 0
            self._update()
            return False

    def set_greenroom(self):
        """ Enables/disables greenroom setting.

        :return: True if enabled else False.
        :rtype: bool
        """
        if not self._form_data['greenroom']:
            self._form_data['greenroom'] = 1
            self._update()
            return True
        elif self._form_data['greenroom']:
            self._form_data['greenroom'] = 0
            self._update()
            return False

    def current_settings(self):
        """ Returns a dictionary of the current room settings.

        :return A dictionary with the following keys: 'broadcast_pass', 'room_pass', 'allow_guest',
        'show_on_directory', 'push2talk', 'greenroom'
        :rtype: dict
        """
        self.parse_privacy_settings()

        settings = dict()
        if self._broadcast_password or self._broadcast_pass_enabled:
            settings['broadcast_pass'] = 'Enabled'
        else:
            settings['broadcast_pass'] = 'Disabled'
        if self._room_password or self._roompass_enabled:
            settings['room_pass'] = 'Enabled'
        else:
            settings['room_pass'] = 'Disabled'

        settings['allow_guest'] = 'No login required'  #
        if self._form_data['allow_guest']:
            if self._form_data['require_twitter'] and self._form_data['require_facebook']:
                settings['allow_guest'] = 'Twitter/Facebook'
            elif self._form_data['require_twitter']:
                settings['allow_guest'] = 'Twitter'
            elif self._form_data['require_facebook']:
                settings['allow_guest'] = 'Facebook'
        if self._room_password:
            settings['show_on_directory'] = 'Hidden'
        else:
            if self._form_data['public_directory']:
                settings['show_on_directory'] = 'Public'
            else:
                settings['show_on_directory'] = 'Hidden'
        if self._form_data['push2talk']:
            settings['push2talk'] = 'Enabled'
        else:
            settings['push2talk'] = 'Disabled'
        if self._form_data['greenroom']:
            settings['greenroom'] = 'Enabled'
        else:
            settings['greenroom'] = 'Disabled'

        return settings

    def _update(self):
        """ Update the privacy page with the current settings.

        This is called when ever a change is made.
        """
        self._form_data['privacy_changes'] = 1
        self._form_data['_token'] = self._csrf_token

        if not self._form_data['allow_guest']:
            del self._form_data['allow_guest']
        if not self._form_data['require_twitter']:
            del self._form_data['require_twitter']
        if not self._form_data['require_facebook']:
            del self._form_data['require_facebook']
        if not self._form_data['public_directory']:
            del self._form_data['public_directory']
        if not self._form_data['push2talk']:
            del self._form_data['push2talk']
        if not self._form_data['greenroom']:
            del self._form_data['greenroom']

        pr = util.web.http_post(post_url=self._privacy_url, post_data=self._form_data, referer=self._privacy_url,
                                proxy=self._proxy, follow_redirect=True)
        self.parse_privacy_settings(response=pr)
