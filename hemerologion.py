#!/usr/bin/env python
"""
Generate posts from hemerologion bot

Usage: python hemerologion.py

This just prints formatted text for posts to stdout for copying-and-pasting
so it isn't strictly bot (yet)

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


def load_day_names():
    """Load Greek day names from TSV file"""
    with open("day_names.tsv") as names:
        reader = csv.reader(names, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)

        # Make a dict. The day numbers are the keys, Greek names the values
        return dict([r[0:2] for r in reader])


def load_festivals():
    """Load festivals from TSV file"""
    with open("festivals.tsv") as fests:
        reader = csv.reader(fests, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC)

        return tuple([tuple(r) for r in reader])

        # Make a dict. The day numbers are the keys, Greek names the values
        return dict([((r[0], r[1], r[4]), tuple(r[2:])) for r in reader])


GK_DAY = load_day_names()

FEST = load_festivals()


def today_jdn():
    """Return today's Julian Date."""
    return int(jd.from_gregorian(*datetime.today().timetuple()[0:7]) + 0.5)


def today_year():
    """Return the current day's year"""
    return datetime.today().year


def today_date():
    """Return today's date as YYYY-MM-DD"""
    return ha.as_gregorian(day.jdn).split()[-1]


def get_count_of_days(count, year, from_jdn):
    """Return a list of days of length 'count' after day 'from_jdn'"""

    cal = tuple([d for d in ha.festival_calendar(year) if d.jdn > from_jdn][0:count])
    if len(cal) < count:
        return cal + get_count_of_days(count - len(cal), year + 1, from_jdn)

    return tuple(cal)


def get_calendar(options):
    """Return tuple of days matching options"""
    if options.year:
        return ha.festival_calendar(options.year)

    if options.days:
        return get_count_of_days(options.days, today_year() - 1, today_jdn())

    raise KeyError("No Valid Option")


def despan(name, span):
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
    festivals = sorted(
        single_day_festivals(day) + multiple_day_festivals(day), key=lambda x: x[0]
    )

    if len(festivals):
        return (
            f"\nFestivals in {day.month_name}:\n"
            + "\n".join([f[1] for f in festivals])
            + "\n"
        )

    return ""


def month_summary(day):
    """Format summary of month"""

    if day.month_length == 29:
        return f"\nThis month will have 29 days, which the ancient Greeks called a “hollow month” (κοῖλος μήν) as opposed to a “full month” (πλήρης μήν) of 30.\n"

    return f"\nThis month will have 30 days, which the ancient Greeks called a “full month” (πλήρης μήν) as opposed to a “hollow month” (κοῖλος μήν) of 29.\n"


def year_summary(months):
    """Format summary of year"""

    day = months[0][0]
    year = ha.arkhon_year(day.astronomical_year).split()[-1]
    year_type = "ordinary" if day.year_length < 380 else "intercalary"
    month_count = 12 if day.year_length < 380 else 13

    summary = f"\n{year} will be an {year_type} year of {day.year_length} days, ending on {ha.as_julian(months[-1][-1]).split()[-1]}. As an {year_type} year there will be {month_count} months:\n\n"

    for month in months:
        start = " ".join(ha.as_julian(month[0]).split()[-1].split("-")[1:3])
        end = " ".join(ha.as_julian(month[-1]).split()[-1].split("-")[1:3])
        summary += f"{month[0].month_name}: {start}–{end}\n"

    return summary


def festivals(day, fests):
    """Return description of festival on given day if needed"""
    in_month = [f for f in fests if f[0] == day.month and f[1] == day.day]

    if not in_month:
        return ""

    post = "\n" + "\n".join([f[2] for f in in_month]) + "\n"
    links = [f[3] for f in in_month if f[3] is not None]

    if links:
        return post + "\n" + "\n".join(links) + "\n"

    return post


def doy_count(day):
    """Format DOY part of post"""
    year = ha.arkhon_year(day.astronomical_year).split()[-1]

    if day.doy == 1:
        return f"day {day.doy} of {day.year_length}. Happy New Year {year}!"

    if day.doy == day.year_length:
        return f"the last day of {year}!"

    return f"day {day.doy} of {day.year_length} in the year {year}."


def to_genitive(month):
    """Convert month name to genitive case"""
    return re.sub(r"ὕστερος", "ὑστέρου", re.sub(r"ών", "ῶνος", month))


def greek_day_name(day):
    """Return formatted name of the day in Greek"""
    if day.day <= 20:
        return GK_DAY[day.day]

    # Omit one day from count in hollow months
    if day.month_length == 29:
        return GK_DAY[day.day + 1]

    # Don't omit in full months
    return GK_DAY[day.day]


def greek_date(day):
    """Return date in Greek"""
    month_gen = to_genitive(ha.month_name(day.month, name_as=ha.MonthNameOptions.GREEK))
    day_gk = greek_day_name(day)
    return f"{day_gk} {month_gen}"


def postulate(day):
    """Craft a post for the given day"""

    post = (
        f"Today is {day.month_name} {day.day} ({greek_date(day)}), {doy_count(day)}\n"
    )

    if day.day == 1:
        post += month_summary(day) + festival_summary(day)

    if day.doy == 1:
        post += year_summary(ha.by_months(ha.festival_calendar(day.astronomical_year)))

    post += festivals(day, FEST)

    return post


def header(post, show_chars):
    if show_chars:
        return f"{today_date()} ({len(post)} chars)"

    return today_date()


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

    args = parser.parse_args()

    for day in get_calendar(args):
        post = postulate(day)
        print(header(post, args.characters))
        print(f"-" * 30)
        print(postulate(day))
