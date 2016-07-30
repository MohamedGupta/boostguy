#!/usr/bin/env python
import twitter, twitter_config, slack_config
import requests, json
from os import path
from slacker import Slacker
import pickle

targetfile = '/home/pi/git/boostguy/targets.p'
sincefile = '/home/pi/git/boostguy/since_ids.p'

cred = next(acct for acct in twitter_config.accounts if acct['username'] == 'BoostedThat4ya')
if path.isfile(targetfile):
    targets = pickle.load(open(targetfile, 'r'))
if path.isfile(sincefile):
    since_ids = pickle.load(open(sincefile, 'r'))
else:
    since_ids = dict()
slack = Slacker(slack_config.key)

def boost_tweets(api):
    if not targets:
        print 'No targets'
        return
    
    for target in targets:
        if target in since_ids:
            since_id = since_ids[target]
        else:
            since_id = 0
        try:
            tweets = api.GetUserTimeline(screen_name=target, since_id=since_id, include_rts=False)
        except twitter.error.TwitterError:
            slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
            targets.remove(target)
            print 'Remaining targets: {0}'.format(', '.join(targets))
            pickle.dump(targets, open(targetfile, 'wb'))
            return

    if len(tweets)==0:
        print 'No new tweets'
    else:
        new_since_id = tweets[0].AsDict()['id']
        try:
            api.PostRetweet(status_id=new_since_id)
        except:
            print 'Already retweeted {0}'.format(new_since_id)
        since_ids[target] = new_since_id
    pickle.dump(since_ids, open(sincefile, 'wb'))


if __name__ == '__main__':
    try:
        api = twitter.Api(consumer_key=cred['consumer_key'], consumer_secret=cred['consumer_secret'],
                          access_token_key=cred['access_token_key'], access_token_secret=cred['access_token_secret'])
    except:
        print 'Failed to authenticate.'
        exit()

    boost_tweets(api)

