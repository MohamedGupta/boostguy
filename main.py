#!/usr/bin/env python
import twitter, twitter_config, slack_config, requests, json, pickle
from os import path
from slacker import Slacker


def boost_tweets(tw, slack):
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

    if not targets:
        print 'No targets'
        return

    for blocked_target in [b for b in blocks if b in targets]:
        targets.remove(blocked_target)

    for target in targets:
        try:
            tw.CreateFriendship(screen_name=target)
        except twitter.error.TwitterError, e:
            if e[0][0]['code'] == 88:
                slack.chat.post_message('#testbed', 'Rate limited')
                return
            elif e[0][0]['code'] in (136, 162):
                blocks.append(target)
                slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
                slack.chat.post_message('#signalboost', 'Cowards: ' + ':troll: '.join(blocks) + ' :troll:')
                targets.remove(target)
                targets.next()
                continue

        if target in since_ids:
            since_id = since_ids[target]
        else:
            since_id = 0

        try:
            tweets = tw.GetUserTimeline(screen_name=target, since_id=since_id, include_rts=False)
        except twitter.error.TwitterError, e:
            if e[0][0]['code'] == 88:
                slack.chat.post_message('#testbed', 'Rate limited')
                return
            elif e[0][0]['code'] in (136, 162):
                blocks.append(target)
                slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
                slack.chat.post_message('#signalboost', 'Cowards: ' + ':troll: '.join(blocks) + ' :troll:')
                targets.remove(target)
                continue
            else:
                slack.chat.post_message('#testbed', 'User timeline for {0} {1}'.format(target, e))
            continue

        if since_id == 0:
            tweets = [tweets[0]]
            since_ids[target] = tweets[0].AsDict()['id']

        for tweet in reversed(tweets):
            try:
                tw.PostRetweet(status_id=tweet.AsDict()['id'])
                since_ids[target] = tweet.AsDict()['id']
            except twitter.error.TwitterError, e:
                if e[0][0]['code'] == 88:
                    slack.chat.post_message('#testbed', 'Rate limited')
                    return
                elif e[0][0]['code'] in (136, 162):
                    blocks.append(target)
                    targets.remove(target)
                    slack.chat.post_message('#testbed', 'Blocked on RT by ' + target + '\n' + e)
                elif e[0][0]['code'] in (327):
                    since_ids[target] = tweet.AsDict()['id']
                else:
                    slack.chat.post_message('#testbed', e)

    targets = [t for t in set(targets)]
    pickle.dump(targets, open(targetfile, 'wb'))
    pickle.dump(since_ids, open(sincefile, 'wb'))
    pickle.dump([b for b in set(blocks)], open(blockfile, 'wb'))

if __name__ == '__main__':
    cred = next(acct for acct in twitter_config.accounts if acct['username'] == 'BoostedThat4ya')
    try:
        tw = twitter.Api(consumer_key=cred['consumer_key'], consumer_secret=cred['consumer_secret'],
                          access_token_key=cred['access_token_key'], access_token_secret=cred['access_token_secret'])
        slack = Slacker(slack_config.key)
    except Exception, e:
        print e
        exit()

    boost_tweets(tw, slack)
