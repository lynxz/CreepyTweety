#!/usr/bin/env python
'''
Created on Jan 4, 2013

@author: lynxz
'''

import oauth2 as oauth
import httplib2
import urlparse
import json
from time import time, sleep

USER_TIMELINE_URL = 'https://api.twitter.com/1.1/statuses/user_timeline.json'

CONSUMER_KEY = 'HAgdrAVwYrtn4enya9ow'
CONSUMER_SECRET = 'kyhCttZf1mL8VJ2P1hEvZPIr35WbsX98mgGb8xTg4'

TOKEN_FILE = 'access_tokens.dat'

class TweetClient(oauth.Client):
    '''
    This class can be used to fetch twitter tweets from a specific individual
    '''

    def __init__(self, sign_method = oauth.SignatureMethod_HMAC_SHA1(), cache=None, timeout=None, proxy_info=None):
        '''
        Constructor
        '''
        self.consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
        super(TweetClient, self).__init__(oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET))
        
        self.ACCESS_TOKEN_KEY = ''
        self.ACCESS_TOKEN_SECRET = ''
        self.sign_method = sign_method
        self.limit_reached = False
        self.renewed_limit_time = 0.0
        
    
    def __read_tokens(self):
        with open(TOKEN_FILE, 'r') as f:
            self.ACCESS_TOKEN_KEY = f.readline().rstrip('\n')
            self.ACCESS_TOKEN_SECRET = f.readline().rstrip('\n') 
    
    def __write_tokens(self):
        with open(TOKEN_FILE, 'w') as f:
            f.write(self.ACCESS_TOKEN_KEY + '\n')
            f.write(self.ACCESS_TOKEN_SECRET + '\n')

    def __get_tokens(self):

        request_token_url = 'http://twitter.com/oauth/request_token'
        access_token_url = 'http://twitter.com/oauth/access_token'
        authorize_url = 'http://twitter.com/oauth/authorize'

        resp, content = self.request(request_token_url, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])

        request_token = dict(urlparse.parse_qsl(content))

        print "Request Token:"
        print "    - oauth_token        = %s" % request_token['oauth_token']
        print "    - oauth_token_secret = %s" % request_token['oauth_token_secret']
        print 

        print "Go to the following link in your browser:"
        print "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
        print 

        accepted = 'n'
        while accepted.lower() == 'n':
            accepted = raw_input('Have you authorized me? (y/n) ')
        oauth_verifier = raw_input('What is the PIN? ')

        self.token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        self.token.set_verifier(oauth_verifier)

        resp, content = self.request(access_token_url, "POST")
        access_token = dict(urlparse.parse_qsl(content))

        print "Access Token:"
        print "    - oauth_token        = %s" % access_token['oauth_token']
        print "    - oauth_token_secret = %s" % access_token['oauth_token_secret']
        print
        print "You may now access protected resources using the access tokens above." 
        print
        
        self.ACCESS_TOKEN_KEY = access_token['oauth_token']
        self.ACCESS_TOKEN_SECRET = access_token['oauth_token_secret']
        self.__write_tokens()
        
    
    def __fetch_data(self, url, http_method = "GET", body = '', headers = None):
        '''
        Fetches data from a specific url using the specified http_method. Body and headers can also be supplied.
        Raises an exception if the http call fails.
        '''
        
        if self.limit_reached:
            sleep_time_in_seconds = self.renewed_limit_time - time()
            if sleep_time_in_seconds > 0:
                print 'sleeping for %.2f.' % (sleep_time_in_seconds / 60.0)
                sleep(int(sleep_time_in_seconds) + 60)
        
        resp, content = httplib2.Http.request(self, url, method=http_method, body=body, headers=headers)
        self.renewed_limit_time = float(resp['x-rate-limit-reset'])
        print 'Remaining queries: %s' % resp['x-rate-limit-remaining']
        print 'Remaining time for limit reset: %.2f' % ((float(resp['x-rate-limit-reset']) - time()) / 60.0)
        
        if int(resp['x-rate-limit-remaining']) == 0:
            sleep_time_in_seconds = self.renewed_limit_time - time()
            if sleep_time_in_seconds > 0:
                print 'sleeping for %.2f.' % (sleep_time_in_seconds / 60.0)
                sleep(int(sleep_time_in_seconds) + 60)
        
        if resp['status'] != '200':
            raise IOError("Invalid Response %s." % resp['status'])
        return content
        
    
    def __create_signed_request(self, url, http_method = "GET", body = '', parameters = {}, headers = None):
        req = oauth.Request.from_consumer_and_token(self.consumer,
                                                    token=self.token, 
                                                    http_method=http_method, 
                                                    http_url=url,
                                                    parameters=parameters, 
                                                    body=body)
        req.sign_request(self.sign_method, self.consumer, self.token)
        return req

    def setup(self):
        try:
            self.__read_tokens() #Reads tokens from a file
        except:
            self.__get_tokens() #Does the Twitter/OAuth three legged authentication
            
        self.token = oauth.Token(self.ACCESS_TOKEN_KEY, self.ACCESS_TOKEN_SECRET)
            

    def fetch_user_tweets(self, user_name, count = 20):
        parameters = {'screen_name': user_name,}
        data = []
        max_id = -1

        if count > 3200:
            raise Exception('Twitter 1.1 REST API only allows 3200 GET calls to a user timeline. %d is to many.' % count)
            
        while count > 0:
            if count > 200:
                parameters['count'] = 200
                count -= 200
            else:
                parameters['count'] = count
                count = 0
            
            if max_id != -1:
                max_id -= 1  #By removing one we avoid getting the same tweet twice.
                parameters['max_id'] = max_id
                
            req = self.__create_signed_request(USER_TIMELINE_URL, parameters = parameters)
            partial_data = json.loads(self.__fetch_data(req.to_url()))
            data.extend(partial_data)
            if len(partial_data) == 200:
                max_id = long(partial_data[199]['id'])
            
        return data
        
    
