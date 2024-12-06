#!/usr/bin/env python
"""Post hemerologion bot posts

Read posts from TSV file, find posts to be posted today and post them
to Mastodon and Bluesky

This requires some environment variable to be set:

    MASTODON: Must be set to some true value to enable posting
    MASTODON_KEY: Key for Mastodon app
    MASTODON_SECRET: Secret for Mastodon app
    MASTODON_TOKEN: Token for Mastodon app

    BLUESKY: Must be set to some true value to enable posting
    BLUESKY_ID: ID of Bluesky user to post as
    BLUESKY_PASSWORD: Password for BLUESKY_ID user

Heavily indebted to https://github.com/thisisparker/oldroadside for
practical understanding of these APIs!

Copyright (C) 2023 Sean Redmond

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
import argparse
import csv
from datetime import datetime, timezone
from mastodon import Mastodon
import os
import requests
import sys
import time
#from atproto import Client, client_utils


class HemerologionPostError(Exception):
    pass


BLUESKY_BASE = "https://bsky.social/xrpc"
MASTODON_BASE = "https://botsin.space"
UA = "hemerologion-post"


def load_posts(fn):
    """Load existing posts from TSV file"""
    with open(fn) as posts:
        reader = csv.reader(posts, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)
        return tuple([tuple(r) for r in reader])


def post_date(d=None):
    """Return datetime in year/month/day format"""
    if d:
        return d

    return datetime.now().strftime("%Y-%b-%d")


def posts_for_day(date, posts):
    """Return only posts matching the given date"""
    return tuple([p for p in posts if p[1] == date])


def get_visibility(private):
    """Return requested visibility for Mastodon."""
    if private:
        return "direct"

    return "public"


def do_bluesky(opts):
    """Check whether Bluesky posting is enabled"""
    # if opts.test:
    #     return opts.bluesky and os.environ.get("BLUESKY", False)

    return int(os.environ.get("BLUESKY", 0))


def do_mastodon(opts):
    """Check whether Mastodon posting is enabled"""
    # if opts.test:
    #     return opts.mastodon and os.environ.get("MASTODON", False)

    return int(os.environ.get("MASTODON", 0))


def post_to_bluesky(post):
    """Post to Bluesky"""

    # client = Client()
    # profile = client.login(os.environ["BLUESKY_ID"], os.environ["BLUESKY_PASSWORD"])
    # #print('Welcome,', profile.display_name)

    
    # text = client_utils.TextBuilder().text(post[3]) #.link('Python SDK', 'https://atproto.blue')

    #print(text)
    #bsky_post = client.send_post(text)

    try:
        resp = requests.post(
            BLUESKY_BASE + "/com.atproto.server.createSession",
            json={
                "identifier": os.environ["BLUESKY_ID"],
                "password": os.environ["BLUESKY_PASSWORD"],
            },
        )

        resp.raise_for_status()

        resp_data = resp.json()
        jwt = resp_data["accessJwt"]
        did = resp_data["did"]

    except requests.exceptions.HTTPError as e:
        raise HemerologionPostError(f"Failed to authenticate to Bluesky {e}")

    iso_timestamp = datetime.now(timezone.utc).isoformat()
    iso_timestamp = iso_timestamp[:-6] + "Z"

    post_data = {
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": {
            "$type": "app.bsky.feed.post",
            "text": post,
            "createdAt": iso_timestamp,
        },
    }

    headers = {"Authorization": "Bearer " + jwt, "User-Agent": UA}

    try:
        resp = requests.post(
            BLUESKY_BASE + "/com.atproto.repo.createRecord",
            json=post_data,
            headers=headers,
        )

        print(resp)
        resp.raise_for_status()

    except requests.exceptions.HTTPError as e:
        raise HemerologionPostError("Failed to post to Bluesky ({})".format(e))

    return "posted to Bluesky"


def post_to_mastodon(post, vis="public"):
    """Post to Mastodon"""
    mastodon = Mastodon(
        client_id=os.environ["MASTODON_KEY"],
        client_secret=os.environ["MASTODON_SECRET"],
        access_token=os.environ["MASTODON_TOKEN"],
        api_base_url=MASTODON_BASE,
        user_agent=UA,
    )

    mastodon.status_post(post, visibility=vis, language="en")

    return "Posted to Mastodon"


def show_posts(p, args):
    print("-" * 60)
    print(f"#{int(p[0])} {p[1]} ({int(p[2])} characters)")
    print("=" * 35)
    print(p[3].replace("\\n", "\n"))
    print("-" * 60)


def post_bluesky(post, args):
    if not do_bluesky(args):
        return

    return post_to_bluesky(post[3].replace("\\n", "\n"))
    

def post_mastodon(post, args):
    if not do_mastodon(args):
        return

    return post_to_mastodon(post[3].replace("\\n", "\n"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="hemerologion",
        description="Post Greek calendar bot posts",
        epilog="""
Posting to Bluesky and Mastodon requires the BLUESKY and MASTODON environment
variable, respectively, set to true values (i.e., MASTODON=1).
""",
    )

    subparsers = parser.add_subparsers(dest="command")

    show_parser = subparsers.add_parser("show", help="Show what would be posted")
    show_parser.set_defaults(func=show_posts)

    post_parser = subparsers.add_parser("post", help="Post")

    post_subparsers = post_parser.add_subparsers(dest="platform")

    
    bluesky_parser = post_subparsers.add_parser("bluesky", help="Post to Bluesky")
    bluesky_parser.set_defaults(func=post_bluesky)
    mastodon_parser = post_subparsers.add_parser("mastodon", help="Post to Mastodon") 
    mastodon_parser.set_defaults(func=post_mastodon)

    parser.add_argument("tsv", metavar="FILE", type=str, help="TSV file for posts")

    parser.add_argument(
        "-d",
        "--for-date",
        metavar="DATE",
        type=str,
        default=post_date(),
        help="Posts for day",
    )

    parser.add_argument(
        "--private",
        action="store_true",
        default=False,
        help="Make post private (Mastodon, = 'direct')",
    )

    args = parser.parse_args()

    posts = posts_for_day(args.for_date, load_posts(args.tsv))

    for p in posts:
        args.func(p, args)

