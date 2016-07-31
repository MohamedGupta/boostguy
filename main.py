#!/usr/bin/env python
import twitter, twitter_config, slack_config, requests, json, pickle
from os import path
from slacker import Slacker


def boost_tweets(api):
    targetfile = '/home/pi/git/boostguy/targets.p'
    sincefile = '/home/pi/git/boostguy/since_ids.p'
    blockfile = '/home/pi/git/boostguy/blocks.p'

    if path.isfile(targetfile):
        targets = pickle.load(open(targetfile, 'r'))
    else:
        targets = []
    if path.isfile(sincefile):
        since_ids = pickle.load(open(sincefile, 'r'))
    else:
        since_ids = dict()
    if path.isfile(blockfile):
        blocks = pickle.load(open(blockfile, 'r'))
    else:
        blocks = []

    slack = Slacker(slack_config.key)

    if not targets:
        print 'No targets'
        return

    for target in targets:
        try:
            api.CreateFriendship(screen_name=target)
        except twitter.error.TwitterError, e:
            if e[0][0]['code'] == 162:
                blocks.append(target)
                slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
                slack.chat.post_message('#signalboost', 'Cowards: ' + ':troll: '.join(blocks) + ' :troll:')
                targets.remove(target)
            if e[0][0]['code'] == 88:
                print 'Rate limited!'
        
        if target not in blocks:
            if target in since_ids:
                since_id = since_ids[target]
            else:
                since_id = 0

            try:
                tweets = api.GetUserTimeline(screen_name=target, since_id=since_id, include_rts=False)
                if len(tweets) == 0:
                    print 'No new tweets for ' + target
                else:
                    new_since_id = tweets[0].AsDict()['id']
                    for tweet in tweets:
                        try:
                            api.PostRetweet(status_id=tweet.AsDict()['id'])
                            since_ids[target] = new_since_id
                        except twitter.error.TwitterError, e:
                            if e[0][0]['code'] == 162:
                                blocks.append(target)
                                slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
                                slack.chat.post_message('#signalboost', 'Cowards: ' + ':troll: '.join(blocks) + ' :troll:')
                                targets.remove(target)
                            if e[0][0]['code'] == 88:
                                print 'Rate limited!'

            except twitter.error.TwitterError, e:
                print e[0][0]
                if e[0][0]['code'] == 162:
                    blocks.append(target)
                    slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
                    slack.chat.post_message('#signalboost', 'Cowards: ' + ':troll: '.join(blocks) + ' :troll:')
                    targets.remove(target)
        else:
            print 'Checking {0} for some reason...'.format(target)
            slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
            slack.chat.post_message('#signalboost', 'Cowards: ' + ':troll: '.join(blocks) + ' :troll:')

    targets = [t for t in set(targets)]
    pickle.dump(targets, open(targetfile, 'wb'))
    pickle.dump(since_ids, open(sincefile, 'wb'))
    pickle.dump([b for b in set(blocks)], open(blockfile, 'wb'))


if __name__ == '__main__':
    cred = next(acct for acct in twitter_config.accounts if acct['username'] == 'BoostedThat4ya')
    try:
        api = twitter.Api(consumer_key=cred['consumer_key'], consumer_secret=cred['consumer_secret'],
                          access_token_key=cred['access_token_key'], access_token_secret=cred['access_token_secret'])
    except:
        print 'Failed to authenticate.'
        exit()

    boost_tweets(api)
