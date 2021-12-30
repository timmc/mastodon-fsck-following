#!/usr/bin/python3

"""
Check your Following list on Mastodon for problems.

So far, just detects moved accounts and reports them.

Desiderata:

- Offer to follow new location of moved accounts (if not already followed)
- Offer to unfollow old location of moved accounts

Requirements:
- First time setup: Install requirements in virtualenv. Using Python 3.9
  as example, though other 3.x versions should work too:
  ```
  python3.9 -m venv .venv39
  source .venv39/bin/activate
  pip install -r requirements.txt
  ```
- OAuth application registered in account. See Development tab in Mastodon
  settings to register one and get an access token with permissions as
  indicated below.

Usage: `.venv39/bin/python -m mastodon-fsck-following <config-file>`

Config file is JSON with the following keys:

- `server` - instance domain e.g. `botsin.space`
- `account_id` - your account ID, a numeric string. Find it in the web app's URL
  when you visit your own profile.
- `token` - Access token with `read:follows` and `read:accounts` permissions

Example:

```
{
    "server": "botsin.space",
    "account_id": "21245",
    "token": "a0v7na73npyn9nyx38xbh256h9f7kihg68s1101nhnakwcqobcqo9358cb19t59h"
}
```
"""

import sys
import json
from mastodon import Mastodon

class Config:
    api = None # mastodon API instance
    myid = None # User's numeric-string ID

def get_all_following(cnf):
    """
    Get a list of all accounts the user is following, as basic account dicts.
    """
    ret = []
    page = cnf.api.account_following(cnf.myid)
    while page is not None:
        ret.extend(page)
        page = cnf.api.fetch_next(page)
    return ret

def fsck_account(cnf, follow_acct_set, acct):
    """Check over a followed account (dict) and optionally repair it."""
    full = cnf.api.account(acct) # full version of account object has 'moved'
    moved = full.get('moved')
    if moved:
        if moved.acct in follow_acct_set:
            print("Account %s has moved to %s (but you're following that one too)"
                  % (full.acct, moved.acct))
        else:
            print("Account %s has moved to %s"
                  % (full.acct, moved.acct))

def run(cnf):
    follow_accts = get_all_following(cnf)
    follow_acct_set = set([x.acct for x in follow_accts])
    for acct in follow_accts:
        fsck_account(cnf, follow_acct_set, acct)

def configure(args):
    """Given command line args, produce a Config object."""
    if len(args) != 1:
        print("Expected one argument, a config file path.", file=sys.stderr)
        sys.exit(1)
    config_path = args[0]
    config_data = json.load(open(config_path))
    mastodon = Mastodon(
        access_token = config_data['token'],
        api_base_url = 'https://' + config_data['server'],
        ratelimit_method = 'wait'
    )
    cnf = Config()
    cnf.api = mastodon
    cnf.myid = config_data['account_id']
    return cnf

def main(args):
    cnf = configure(args)
    run(cnf)

if __name__ == "__main__":
    main(sys.argv[1:])
