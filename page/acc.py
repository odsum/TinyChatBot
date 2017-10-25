from bs4 import BeautifulSoup
import util.web


class Account:
    """ This class contains methods to do login/logout and check if logged in or not. """
    def __init__(self, account, password, proxy=None):
        """ Create a instance of the Account class.

        :param account: Tinychat account name.
        :type account: str
        :param password: Tinychat account password.
        :type password: str
        :param proxy: A proxy in the format IP:PORT
        :type proxy: str
        """
        self.account = account
        self.password = password
        self._proxy = proxy
        self._token = None

    def _parse_token(self, response=None):
        """ Parse the token needed for the HTTP login POST.

        :param response: A html response.
        :type response: dict
        """
        token_url = 'https://tinychat.com/start?#signin'
        if response is None:
            response = util.web.http_get(url=token_url, referer=token_url, proxy=self._proxy)

        if response is not None and response['content'] is not None:
            soup = BeautifulSoup(response['content'], 'html.parser')

            token = soup.find(attrs={'name': 'csrf-token'})
            self._token = token['content']

    @staticmethod
    def logout():
        """ Log out of tinychat. """
        _cookies = ['user', 'pass', 'hash']
        for cookie in _cookies:
            util.web.delete_cookie(cookie)

    @staticmethod
    def is_logged_in():
        """ Check if logged in to tinychat.

        :return True if logged in, else False.
        :rtype: bool
        """
        _has_cookie = util.web.has_cookie('pass')
        if _has_cookie:
            _is_expired = util.web.is_cookie_expired('pass')
            if _is_expired:
                return False
            return True
        return False

    def login(self):
        """ Makes a HTTP login POST to tinychat. """
        if self._token is None:
            self._parse_token()

        _post_url = 'https://tinychat.com/login'

        form_data = {
            'login_username': self.account,
            'login_password': self.password,
            'remember': '1',
            'next': 'https://tinychat.com/',
            '_token': self._token
        }

        login_response = util.web.http_post(post_url=_post_url, post_data=form_data,
                                            follow_redirect=True, proxy=self._proxy)
        self._parse_token(response=login_response)

        # return login_response
