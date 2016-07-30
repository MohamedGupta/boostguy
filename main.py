#!/usr/bin/env python
import twitter, twitter_config
import requests, json
from os import path

cred = next(acct for acct in twitter_config.accounts if acct['username'] == 'BoostedThat4ya')
target = open('target', 'r').read()


def boost_tweets(api):
    if path.isfile('since_id'):
        since_id = open('since_id', 'r').read()
    else:
        since_id = 0
    tweets = api.GetUserTimeline(screen_name=target, since_id=since_id, include_rts=False)
    if len(tweets)==0:
        print 'No new tweets'
    else:
        new_since_id = tweets[0].AsDict()['id']
        api.PostRetweet(status_id=new_since_id)
        with open('since_id', 'w') as file:
            file.write(str(new_since_id))


if __name__ == '__main__':
    try:
        api = twitter.Api(consumer_key=cred['consumer_key'], consumer_secret=cred['consumer_secret'],
                          access_token_key=cred['access_token_key'], access_token_secret=cred['access_token_secret'])
    except:
        print 'Failed to authenticate.'
        exit()

    boost_tweets(api)

