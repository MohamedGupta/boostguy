#!/usr/bin/env python
import twitter, twitter_config, slack_config
import requests, json
from os import path
from slacker import Slacker

targetfile = '/home/pi/git/boostguy/target.txt'
sincefile = '/home/pi/git/boostguy/since_id.txt'

cred = next(acct for acct in twitter_config.accounts if acct['username'] == 'BoostedThat4ya')
target = open(targetfile, 'r').read()
slack = Slacker(slack_config.key)

def boost_tweets(api):
    if not target:
        print 'No target'
        return
    if path.isfile(sincefile):
        since_id = open(sincefile, 'r').read()
    else:
        since_id = 0
    try:
        tweets = api.GetUserTimeline(screen_name=target, since_id=since_id, include_rts=False)
    except twitter.error.TwitterError:
        slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
        with open(targetfile, 'w') as file:
            file.write('')        
        return

    if len(tweets)==0:
        print 'No new tweets'
    else:
        new_since_id = tweets[0].AsDict()['id']
        api.PostRetweet(status_id=new_since_id)
        with open(sincefile, 'w') as file:
            file.write(str(new_since_id))


if __name__ == '__main__':
    try:
        api = twitter.Api(consumer_key=cred['consumer_key'], consumer_secret=cred['consumer_secret'],
                          access_token_key=cred['access_token_key'], access_token_secret=cred['access_token_secret'])
    except:
        print 'Failed to authenticate.'
        exit()

    boost_tweets(api)

