import pytest
import hemerologion as hem
from collections import namedtuple

Day = namedtuple("Day", ("month", "day", "month_length"))


def test_get_single_festival_for_day():
    fests = hem.festivals_by_day(Day(1, 12, 30))
    assert len(fests) == 1
    assert fests[0][4] == "Kronia"


def test_get_multiple_festivals_for_day():
    fests = hem.festivals_by_day(Day(4, 6, 30))
    assert len(fests) == 2
    assert fests[0][4] == "Proerosia"
    assert fests[1][4] == "Oskhoporia"


def test_festival_hene_kai_nea():
    # 29th of a hollow month
    fest = hem.festivals_by_day(Day(4, 29, 29))
    assert fest[0][4] == "Kalkheia"

    # 30th of a full month
    fest = hem.festivals_by_day(Day(4, 30, 30))
    assert fest[0][4] == "Kalkheia"

    # not 29th of a hollow month
    assert not hem.festivals_by_day(Day(4, 29, 30))


def test_backwards_count():
    # Forward count
    assert hem.backwards_count(Day(1, 21, 30)) == 21
    assert hem.backwards_count(Day(1, 21, 29)) == 21

    # Full month
    assert hem.backwards_count(Day(1, 30, 30)) == -1
    assert hem.backwards_count(Day(1, 29, 30)) == 29
    assert hem.backwards_count(Day(1, 28, 30)) == 28

    # Hollow month
    assert hem.backwards_count(Day(1, 29, 29)) == -1
    assert hem.backwards_count(Day(1, 28, 29)) == 28

    # Hollow month omits it
    with pytest.raises(ValueError):
        hem.backwards_count(Day(1, 30, 29))


def test_greek_day_name():
    assert hem.greek_day_name(Day(1, 1, 30)) == "νουμηνίᾳ"
    assert hem.greek_day_name(Day(1, 1, 29)) == "νουμηνίᾳ"

    assert hem.greek_day_name(Day(1, 20, 30)) == "δεκάτῃ προτέρᾳ"
    assert hem.greek_day_name(Day(1, 20, 29)) == "δεκάτῃ προτέρᾳ"

    assert hem.greek_day_name(Day(1, 21, 30)) == "δεκάτῃ ὑστέρᾳ"
    assert hem.greek_day_name(Day(1, 21, 29)) == "δεκάτῃ ὑστέρᾳ"

    assert hem.greek_day_name(Day(1, 28, 30)) == "τρίτῃ φθίνοντος"
    assert hem.greek_day_name(Day(1, 29, 30)) == "δευτέρᾳ φθίνοντος"
    assert hem.greek_day_name(Day(1, 30, 30)) == "ἕνῃ καὶ νέᾳ"

    # Omit δευτέρᾳ φθίνοντος in a hollow month
    assert hem.greek_day_name(Day(1, 28, 29)) == "τρίτῃ φθίνοντος"
    assert hem.greek_day_name(Day(1, 29, 29)) == "ἕνῃ καὶ νέᾳ"
