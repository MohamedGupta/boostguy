#!/usr/bin/env python
import twitter, twitter_config, slack_config, requests, json, pickle
from os import path
from slacker import Slacker


def boost_tweets(tw, slack):
    targetfile = '/home/pi/git/boostguy/targets.p'
    sincefile = '/home/pi/git/boostguy/since_ids.p'
    blockfile = '/home/pi/git/boostguy/blocks.p'
    retweetfile = '/home/pi/git/boostguy/retweets.p'

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
    if path.isfile(retweetfile):
        retweets = pickle.load(open(retweetfile, 'r'))
    else:
        retweets = dict()

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
                retweets[target] = []
                since_ids[target] = 0
                slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
                slack.chat.post_message('#signalboost', 'Cowards: ' + ':troll: '.join(blocks) + ' :troll:')
                targets.remove(target)
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
                pickle.dump(retweets, open(retweetfile, 'wb'))
                pickle.dump([t for t in set(targets)], open(targetfile, 'wb'))
                pickle.dump(since_ids, open(sincefile, 'wb'))
                pickle.dump([b for b in set(blocks)], open(blockfile, 'wb'))
                return
            elif e[0][0]['code'] in (136, 162):
                blocks.append(target)
                retweets[target] = []
                since_ids[target] = 0
                slack.chat.post_message('#signalboost', 'Signal boost guy has been blocked by ' + target)
                slack.chat.post_message('#signalboost', 'Cowards: ' + ':troll: '.join(blocks) + ' :troll:')
                targets.remove(target)
                continue
            else:
                slack.chat.post_message('#testbed', 'User timeline for {0} {1}'.format(target, e))
            continue

        if since_id == 0:
            tweets = [tweets[0]]

        if target not in retweets.keys():
            retweets[target] = list(t.AsDict()['id'] for t in tweets)
        else:
            retweets[target].append(list(t.AsDict()['id'] for t in tweets))

        for tweet_id in reversed(retweets[target]):
            try:
                tw.PostRetweet(status_id=tweet_id)
                since_ids[target] = tweet_id
                retweets[target].remove(tweet_id)
                slack.chat.post_message('#testbed', '```Retweeted {0} {1}```'.format(target, tweet_id))
            except twitter.error.TwitterError, e:
                if e[0][0]['code'] == 88:
                    # Rate Limited
                    slack.chat.post_message('#testbed', 'Rate limited')
                    pickle.dump(retweets, open(retweetfile, 'wb'))
                    pickle.dump([t for t in set(targets)], open(targetfile, 'wb'))
                    pickle.dump(since_ids, open(sincefile, 'wb'))
                    pickle.dump([b for b in set(blocks)], open(blockfile, 'wb'))
                    return
                elif e[0][0]['code'] in (136, 162):
                    # Blocked
                    blocks.append(target)
                    targets.remove(target)
                    slack.chat.post_message('#testbed', 'Blocked on RT by ' + target + '\n' + e)
                elif e[0][0]['code'] == 327:
                    #Already Retweeted
                    since_ids[target] = tweet_id
                else:
                    slack.chat.post_message('#testbed', e)

    pickle.dump(retweets, open(retweetfile, 'wb'))
    pickle.dump([t for t in set(targets)], open(targetfile, 'wb'))
    pickle.dump(since_ids, open(sincefile, 'wb'))
    pickle.dump([b for b in set(blocks)], open(blockfile, 'wb'))

if __name__ == '__main__':
    cred = twitter_config.accounts['BoostedThat4ya']
    try:
        tw = twitter.Api(consumer_key=cred['consumer_key'], consumer_secret=cred['consumer_secret'],
                          access_token_key=cred['access_token_key'], access_token_secret=cred['access_token_secret'])
        slack = Slacker(slack_config.key)
    except Exception, e:
        print e
        print 'Error on init'
        exit()

    boost_tweets(tw, slack)