""" Contains functions to make http GET and http POST with. version 0.0.6 """
import time
import logging
import requests
from requests.utils import quote, unquote

__all__ = ['quote', 'unquote']

log = logging.getLogger(__name__)

#  A session that all requests will use...apparently not.
__request_session = requests.session()


def is_cookie_expired(cookie_name):
    """
    Check if a cookie is expired.

    :param cookie_name: str the name of the cookie to check.
    :return: True if expired else False or None if no cookie by that name was found.
    """
    if cookie_name:
        expires = int
        timestamp = int(time.time())
        for cookie in __request_session.cookies:
            if cookie.name == cookie_name:
                expires = cookie.expires
            else:
                return None
        if timestamp > expires:
            log.debug('cookie[\'%s\'] is expired. time stamp: %s, expires: %s' %
                      (cookie_name, timestamp, expires))
            return True
        log.debug('cookie[\'%s\'] is not expired. time stamp: %s, expires: %s' %
                  (cookie_name, timestamp, expires))
        return False


def delete_cookie(cookie_name):
    """
    Delete a cookie by name.
    :param cookie_name: str the cookie name.
    :return: True if deleted else False
    """
    if cookie_name in __request_session.cookies:
        del __request_session.cookies[cookie_name]
        log.debug('deleting cookie: %s session cookies: %s' % (cookie_name, __request_session.cookies))
        return True
    return False


def has_cookie(cookie_name):
    """
    Check a cookie by name to see if it exist.
    :param cookie_name: str the name of the cookie.
    :return: object request.session.cookie[cookie_name] or False if no cookie.
     """
    if cookie_name in __request_session.cookies:
        log.debug('cookie found: %s' % __request_session.cookies[cookie_name])
        return __request_session.cookies[cookie_name]
    log.debug('no cookie named: %s found.' % cookie_name)
    return False


def http_get(url, **kwargs):
    json = kwargs.get('json', False)
    proxy = kwargs.get('proxy', '')
    header = kwargs.get('header')
    timeout = kwargs.get('timeout', 20)
    referer = kwargs.get('referer')

    default_header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/50.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    if referer is not None:
        default_header['Referer'] = referer

    if header is not None and type(header) is dict:
        default_header.update(header)

    if proxy:
        proxy = {'https': 'http://' + proxy}

    gr = None
    json_response = None

    try:
        gr = __request_session.request(method='GET', url=url, headers=default_header, proxies=proxy, timeout=timeout)
        if json:
            json_response = gr.json()
    except ValueError as ve:
        log.error('error while decoding %s to json: %s' % (url, ve))
    except (requests.ConnectionError, requests.RequestException) as re:
        log.error('http_get error: %s' % re)
    finally:
        log.debug('cookies: %s' % __request_session.cookies)
        if gr is None:
            return dict(content=None, json=None,
                        cookies=None, headers=None, status_code=None)
        else:
            return dict(content=gr.text, json=json_response,
                        cookies=gr.cookies, headers=gr.headers, status_code=gr.status_code)


def http_post(post_url, post_data, **kwargs):
    json = kwargs.get('json', False)
    proxy = kwargs.get('proxy', '')
    header = kwargs.get('header')
    timeout = kwargs.get('timeout', 20)
    referer = kwargs.get('referer')
    stream = kwargs.get('is_stream', False)
    redirect = kwargs.get('follow_redirect', False)

    default_header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/50.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    if referer is not None:
        default_header['Referer'] = referer

    if not post_url:
        raise ValueError('no post_url provided. post_url=%s' % post_url)
    elif proxy and type(proxy) is not str:
        raise TypeError('proxy must be of type str and in the format ip:port. proxy type=%s'
                        % type(proxy))
    else:
        if header is not None and type(header) is dict:
            default_header.update(header)

        if proxy:
            proxy = {'http': 'http://' + proxy}

        pr = None
        json_response = None

        try:
            pr = __request_session.request(method='POST', url=post_url, data=post_data, headers=default_header,
                                           allow_redirects=redirect, proxies=proxy, timeout=timeout, stream=stream)
            if json:
                json_response = pr.json()
        except ValueError as ve:
            log.error('error while decoding %s to json: %s' % (post_url, ve))
        except (requests.HTTPError, requests.RequestException) as pe:
            log.error('http_post error %s' % pe)
        finally:
            log.debug('cookies: %s' % __request_session.cookies)
            if pr is None:
                return dict(content=None, json=None,
                            cookies=None, headers=None, status_code=None)
            else:
                return dict(content=pr.text, json=json_response,
                            cookies=pr.cookies, headers=pr.headers, status_code=pr.status_code)
