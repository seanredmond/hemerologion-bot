#!/usr/bin/env python
"""Generate posts from hemerologion bot

Usage: python hemerologion.py

Print tab-delimited rows to stdout (redirect to save) for daily posting by
hemerologion-bot.

The columns are:

    1: And serial index number
    2: The date for the post (there may be multiple posts for a day)
    3: The character count of the post
    4: The text for the post

Alternately just show what the posts will be (with --no-csv).

By default it generates posts for the next 10 days, starting with the next day.
The number of days can be changed via the -d parameter.

With the -y parameter you can generate posts for an entire calendar year.

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
from datetime import datetime
import heniautos as ha
import juliandate as jd
import re
from itertools import groupby
import sys

AMPH = "\U0001F3FA"  # Amphora emoji


def load_day_names():
    """Load Greek day names from TSV file"""
    with open("day_names.tsv", "r") as names:
        reader = csv.reader(names, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)

        # Make a dict. The day numbers are the keys, Greek names the values
        return dict([r[0:2] for r in reader])


def load_festivals():
    """Load festivals from TSV file"""
    with open("festivals.tsv", "r") as fests:
        reader = csv.reader(fests, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)

        return tuple([tuple(r) for r in reader])

        # Make a dict. The day numbers are the keys, Greek names the values
        return dict([((r[0], r[1], r[4]), tuple(r[2:])) for r in reader])


GK_DAY = load_day_names()

FEST = load_festivals()


def get_current_posts(fn):
    """Load existing posts from TSV file"""
    with open(fn, "r") as posts:
        reader = csv.reader(posts, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)

        return tuple([r for r in reader])


def today_jdn():
    """Return today's Julian Date."""
    return int(jd.from_gregorian(*datetime.today().timetuple()[0:7]) + 0.5)


def today_year():
    """Return the current day's year"""
    return datetime.today().year


def gregorian_date(day):
    """Return today's date as YYYY-Mon-DD"""
    return ha.as_gregorian(day.jdn).split()[-1]


def get_count_of_days(count, year, from_jdn):
    """Return a list of days of length 'count' after day 'from_jdn'"""

    cal = tuple(
        [d for d in ha.athenian_festival_calendar(year) if d.jdn > from_jdn][0:count]
    )
    if len(cal) < count:
        return cal + get_count_of_days(count - len(cal), year + 1, from_jdn)

    return tuple(cal)


def get_calendar(options):
    """Return tuple of days matching options"""
    if options.year:
        return ha.athenian_festival_calendar(options.year)

    if options.days:
        return get_count_of_days(options.days, today_year() - 1, today_jdn())

    raise KeyError("No Valid Option")


def despan(name, span):
    """Turn a list of date into a single x–y span"""
    dates = [int(d[0]) for d in span]
    return (min(dates), f"{min(dates)}–{max(dates)}: {name[0]} ({name[1]})")


def single_day_festivals(day):
    """Format summaries of single-day festivals"""
    return tuple(
        [
            (d[1], f"{int(d[1])}: {d[4]} ({d[5]})")
            for d in FEST
            if d[0] == day.month and d[-1] == 1
        ]
    )


def multiple_day_festivals(day):
    """Format summaries of festivals spanning multiple days"""
    spans = groupby(
        [(d[1], d[4], d[5]) for d in FEST if d[0] == day.month and d[-1] > 1],
        key=lambda x: x[1:],
    )
    return tuple([despan(*s) for s in spans])


def festival_summary(day):
    """Summarize festivals occuring in this month"""

    if day.day != 1:
        return ()

    festivals = sorted(
        single_day_festivals(day) + multiple_day_festivals(day), key=lambda x: x[0]
    )

    if len(festivals):
        return (
            f"Festivals in {day.month_name}:\n\n"
            + "\n".join([f[1] for f in festivals]),
        )

    return ()


def month_summary(day):
    """Format summary of month"""
    if day.day != 1:
        return ()

    if day.month_length == 29:
        return (
            f"This {day.month_name} will have 29 days, which the ancient "
            "Greeks called a “hollow month” (κοῖλος μήν) as opposed to a "
            "“full month” (πλήρης μήν) of 30.",
        )

    return (
        f"This {day.month_name} will have 30 days, which the ancient Greeks "
        "called a “full month” (πλήρης μήν) as opposed to a “hollow month” "
        "(κοῖλος μήν) of 29.",
    )


def summary_of_months(months, second_half=False):
    summary = ""
    for month in months[6:] if second_half else months[0:6]:
        start = " ".join(ha.as_julian(month[0]).split()[-1].split("-")[1:3])
        end = " ".join(ha.as_julian(month[-1]).split()[-1].split("-")[1:3])
        summary += f"{month[0].month_name}: {start}–{end}\n"

    return summary


def summarize_first_half(months):
    """Format summary of the first six months of the year."""

    day1 = months[0][0]
    year = ha.arkhon_year(day1.astronomical_year).split()[-1]
    year_type = "ordinary" if day1.year_length < 380 else "intercalary"
    month_count = 12 if day1.year_length < 380 else 13

    if month_count != 12:
        raise ValueError("This does not yet handle intercalary years!!")

    summary1 = (
        f"{year} will be an {year_type} year of {day1.year_length} "
        f"days, ending on {ha.as_julian(months[-1][-1]).split()[-1]}. As an "
        f"{year_type} year there will be {month_count} months (1/2):\n\n"
    )

    for month in months[0:6]:
        start = " ".join(ha.as_julian(month[0]).split()[-1].split("-")[1:3])
        end = " ".join(ha.as_julian(month[-1]).split()[-1].split("-")[1:3])
        summary1 += f"{month[0].month_name}: {start}–{end}\n"

    return summary1


def summarize_second_half(months):
    """Format summary of last six months of the year."""
    year = ha.arkhon_year(months[0][0].astronomical_year).split()[-1]

    summary2 = f"Months in {year} (2/2):\n\n"
    for month in months[6:]:
        start = " ".join(ha.as_julian(month[0]).split()[-1].split("-")[1:3])
        end = " ".join(ha.as_julian(month[-1]).split()[-1].split("-")[1:3])
        summary2 += f"{month[0].month_name}: {start}–{end}\n"

    return summary2


def year_summary(day):
    """Format summary of year."""

    if day.doy != 1:
        return ()

    months = ha.by_months(ha.athenian_festival_calendar(day.astronomical_year))

    # This has to be split into two posts because it is long
    return (summarize_first_half(months), summarize_second_half(months))


def backwards_count(day):
    """Check for last day of month. Return -1 if true"""

    # Use -1 for ἕνη καὶ νέα, whether it is the 29th or 30th
    # We are treating δευτέρα φθίνοντος as the omitted day
    if day.day == day.month_length:
        return -1

    if day.day < day.month_length:
        return day.day

    raise ValueError(
        f"Day number ({day.day}) is greater than the number of days in the month ({day.month_length})"
    )


def festivals_by_day(day):
    """Return festivals for a given day"""
    # Festivals on the last day are recorded as day -1
    day_day = backwards_count(day)
    return [f for f in FEST if f[0] == day.month and f[1] == day_day]


def festivals(day):
    """Return description of festival on given day if needed"""
    in_month = festivals_by_day(day)

    if not in_month:
        return ()

    post = f"{AMPH} " + "\n".join([f[2] for f in in_month])
    links = [f[3] for f in in_month if f[3] is not None]

    if links:
        return (post + "\n\n" + "\n".join(links),)

    return (post,)


def doy_count(day):
    """Format DOY part of post"""
    year = ha.arkhon_year(day.astronomical_year).split()[-1]

    if day.doy == 1:
        return f"day {day.doy} of {day.year_length}. Happy New Year {year}! {AMPH}{AMPH}{AMPH}"

    if day.doy == day.year_length:
        return f"the last day of {year}!"

    return f"day {day.doy} of {day.year_length} in the year {year}."


def to_genitive(month):
    """Convert month name to genitive case"""
    return re.sub(r"ὕστερος", "ὑστέρου", re.sub(r"ών", "ῶνος", month))


def greek_day_name(day):
    """Return formatted name of the day in Greek"""

    if day.day == day.month_length:
        return GK_DAY[30]

    return GK_DAY[day.day]


def greek_date(day):
    """Return date in Greek"""
    month_gen = to_genitive(ha.month_name(day.month, name_as=ha.MonthNameOptions.GREEK))
    day_gk = greek_day_name(day)
    return f"{day_gk} {month_gen}"


def postulate(day):
    """Craft a post for the given day"""

    post = f"Today ({gregorian_date(day)}) is {day.month_name} {day.day}, {greek_date(day)}, {doy_count(day)}"

    return (
        (post,)
        + year_summary(day)
        + month_summary(day)
        + festival_summary(day)
        + festivals(day)
    )


def header(post, show_chars):
    """Format post header for preview output"""
    if show_chars:
        return f"{datetime.today().strftime('%Y-%b-%d')} ({len(post)} chars)"

    return datetime.today().strftime("%Y-%b-%d")


def show_post(post, show_char_count):
    """Format post for preview output"""
    return "\n".join((header(post, args.characters), "-" * 30, post, ""))


def escape(s):
    """Escape newlines for TSV"""
    return s.replace("\n", "\\n")


def unescape(s):
    """Reverse escaped newlines"""
    return s.replace("\\n", "\n")


def max_count(posts):
    """Return the highest serial index in list of posts"""
    if not posts:
        return 0

    return int(max([p[0] for p in posts]))


def jdn_from_date(date):
    """Return JDN from formatted date"""
    return int(
        jd.from_gregorian(*tuple(datetime.strptime(date, "%Y-%b-%d").timetuple())[:3])
        + 0.5
    )


def max_date(posts):
    """Return latest date in list of posts"""
    if not posts:
        return 0

    return max([jdn_from_date(p[1]) for p in posts])


def output_existing(writer, args, after=today_jdn()):
    """Load and output existing rows if requested and necessary"""
    # Load existing post if requested
    try:
        current_posts = get_current_posts(args.file) if args.append else ()
    except TypeError as e:
        if not args.file:
            print(
                "Cannot load exising posts for --append, --file required",
                file=sys.stderr,
            )
            sys.exit(-1)

        raise e

    # Ouput existing posts if there are any
    for post in current_posts:
        if args.keep_old or jdn_from_date(post[1]) >= after:
            if not args.csv:
                print(show_post(unescape(post[3]), args.characters))

            if args.csv:
                writer.writerow((int(post[0]), post[1], int(post[2]), post[3]))

    return (max_count(current_posts) + 1, max_date(current_posts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="hemerologion", description="Generate Greek calendar bot posts"
    )

    parser.add_argument(
        "-d",
        "--days",
        metavar="N",
        type=int,
        default="10",
        help="generate posts for the next N days (default 10)",
    )
    parser.add_argument(
        "-y",
        "--year",
        metavar="Y",
        type=int,
        help="Generate posts for given Julian year (overrides -d)",
    )
    parser.add_argument(
        "-c",
        "--characters",
        action="store_true",
        help="Show character count for each post",
    )

    parser.add_argument(
        "--csv",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Output CSV file",
    )

    parser.add_argument(
        "-a",
        "--append",
        action="store_true",
        help="Append to existing file (with --file)",
    )

    parser.add_argument(
        "--keep-old",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep old posts (with --append,  --file) in output",
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        metavar="FILE",
        help="Existing TSV file",
    )

    args = parser.parse_args()

    writer = csv.writer(sys.stdout, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)
    (count, append_after) = output_existing(writer, args)

    for day in get_calendar(args):
        if day.jdn > append_after:
            for post in postulate(day):

                if not args.csv:
                    print(header(post, args.characters))
                    print("-" * 30)
                    print(post)
                    print()

                if args.csv:
                    writer.writerow(
                        (
                            count,
                            ha.as_gregorian(day.jdn).split()[-1],
                            len(post),
                            escape(post),
                        )
                    )

                count += 1
