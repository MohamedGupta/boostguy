#!/usr/bin/env python
import twitter, twitter_config, settings
import requests, json
cred = next(acct for acct in twitter_config.accounts if acct['username'] == 'FYADFlags')

def tweet_flag(api):
    
    user_blacklist = True
    while user_blacklist == True:
        req = requests.get('http://forums.somethingawful.com/flag.php?forumid=26')
        flag = json.loads(req.content)
        user_blacklist = flag['username'] in settings.blacklist

    flagpath = "http://fi.somethingawful.com/flags" + flag['path']
    tweet = "#FYADflag " + flagpath + " by " + flag['username'] + " " + flag['created']
    mediatweet = "#FYADflag by " + flag['username'] + " " + flag['created'] + " " + flagpath
    
    if flag['path'] != 'error.png':
        try:
            r = api.PostUpdate(mediatweet, media=flagpath)
            print 'Posted flag ' + flagpath
        except:
            print 'Flag post failed ' + flagpath
    else:
        print 'SA PHP error {0}'.format(flag)
if __name__ == '__main__':
    try:
        api = twitter.Api(consumer_key=cred['consumer_key'], consumer_secret=cred['consumer_secret'],
                          access_token_key=cred['access_token_key'], access_token_secret=cred['access_token_secret'])
    except:
        print 'Failed to authenticate.'
        exit()

    tweet_flag(api)

