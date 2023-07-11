#!/usr/bin/env python
"""
Post hemerologion bot posts

Read posts from TSV file, find posts to be posted today and post them to BlueSky

This requires some environment variable to be set:

    BLUESKY: Must be set to some true value to enable posting
    BLUESKY_ID: ID of BlueSky user to post as
    BLUESKY_PASSWORD: Password for BLUESKY_ID user

Heavily indebted to https://github.com/thisisparker/oldroadside for practical 
understanding of these APIs!

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
import os
import requests
import time

BLUESKY_BASE = "https://bsky.social/xrpc"


def load_posts(fn):
    with open(fn) as posts:
        reader = csv.reader(posts, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)
        return tuple([tuple(r) for r in reader])


def post_date(d=None):
    if d:
        return d

    return datetime.now().strftime("%Y-%b-%d")


def posts_for_day(date, posts):
    return tuple([p for p in posts if p[1] == date])


def do_bluesky(opts):
    if args.immediate:
        return args.bluesky and os.environ.get("BLUESKY", False)

    return os.environ.get("BLUESKY", False)


def post_to_bluesky(post):
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
        return f"Failed to authenticate to BlueSky. {e}"

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

    headers = {"Authorization": "Bearer " + jwt}

    try:
        resp = requests.post(
            BLUESKY_BASE + "/com.atproto.repo.createRecord",
            json=post_data,
            headers=headers,
        )

        resp.raise_for_status()

    except requests.exceptions.HTTPError as e:
        return f"Failed to post to BlueSky. {e}"

    return "posted to BlueSky"


def post_posts(post, opts):
    result = ()
    if do_bluesky(opts):
        result = result + (post_to_bluesky(post),)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="hemerologion", description="Generate Greek calendar bot posts"
    )

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
        "-s", "--show", action="store_true", help="Only show what would be posted"
    )

    parser.add_argument(
        "-m",
        "--immediate",
        action="store_true",
        help="Post immediately (with --bluesky and/or --mastodon)",
    )

    parser.add_argument(
        "--bluesky",
        action="store_true",
        default=False,
        help="Post immediately to BlueSky (with --immediate)",
    )

    args = parser.parse_args()

    posts = posts_for_day(args.for_date, load_posts(args.tsv))

    for p in posts:
        if args.show:
            print("-" * 60)
            print(f"#{int(p[0])} {p[1]} ({int(p[2])} characters)")
            print("=" * 35)
            print(p[3].replace("\\n", "\n"))
            print("-" * 60)

        else:
            for r in post_posts(p[3].replace("\\n", "\n"), args):
                print(r)
                time.sleep(1)
