import pytest
import hemerologion as hem
import heniautos as ha
import argparse
from collections import namedtuple

Day = namedtuple("Day", ("month", "day", "month_length"))


@pytest.fixture
def cal_2023():
    options = argparse.Namespace(year=2023)
    return hem.get_calendar(options)


@pytest.fixture
def cal_2024():
    options = argparse.Namespace(year=2024)
    return hem.get_calendar(options)


def test_get_calendar_by_year():
    options = argparse.Namespace(year=2024)
    cal = hem.get_calendar(options)
    assert cal[0].doy == 1
    assert cal[0].jdn == 2460498
    assert cal[-1].doy == 355
    assert cal[-1].jdn == 2460852


def test_get_calendar_by_days():
    options = argparse.Namespace(year=None, days=10)
    cal = hem.get_calendar(options)
    assert len(cal) == 10


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
    assert fest[0][4] == "Khalkeia"

    # 30th of a full month
    fest = hem.festivals_by_day(Day(4, 30, 30))
    assert fest[0][4] == "Khalkeia"

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


def test_summary_of_months(cal_2023):
    months = ha.by_months(cal_2023)
    s = hem.summary_of_months(months).split("\n")
    print(s)
    assert s[0] == "Hekatombaiṓn: Jul 18–Aug 16"
    assert s[1] == "Metageitniṓn: Aug 17–Sep 15" in s
    assert s[2] == "Boēdromiṓn: Sep 16–Oct 14" in s
    assert s[3] == "Puanopsiṓn: Oct 15–Nov 13" in s
    assert s[4] == "Maimaktēriṓn: Nov 14–Dec 12" in s
    assert s[5] == "Posideiṓn: Dec 13–Jan 11" in s
    assert s[6] == ""
    assert len(s) == 7


def test_summary_of_months_second_half(cal_2023):
    months = ha.by_months(cal_2023)
    s = hem.summary_of_months(months, True).split("\n")

    assert s[0] == "Gamēliṓn: Jan 12–Feb 09"
    assert s[1] == "Anthestēriṓn: Feb 10–Mar 10" in s
    assert s[2] == "Elaphēboliṓn: Mar 11–Apr 08" in s
    assert s[3] == "Mounukhiṓn: Apr 09–May 08" in s
    assert s[4] == "Thargēliṓn: May 09–Jun 06" in s
    assert s[5] == "Skirophoriṓn: Jun 07–Jul 05" in s
    assert s[6] == ""


def test_summarize_first_half(cal_2024):
    months = ha.by_months(cal_2024)

    s = hem.summarize_first_half(months)
    assert (
        s
        == "2024/2025 will be an ordinary year of 355 days, ending on 2025-Jun-25. As an ordinary year there will be 12 months (1/2):\n\nHekatombaiṓn: Jul 06–Aug 04\nMetageitniṓn: Aug 05–Sep 03\nBoēdromiṓn: Sep 04–Oct 02\nPuanopsiṓn: Oct 03–Nov 01\nMaimaktēriṓn: Nov 02–Dec 01\nPosideiṓn: Dec 02–Dec 30\n"
    )


def test_summarize_second_half(cal_2024):
    months = ha.by_months(cal_2024)

    s = hem.summarize_second_half(months)
    assert (
        s
        == "Months in 2024/2025 (2/2):\n\nGamēliṓn: Dec 31–Jan 29\nAnthestēriṓn: Jan 30–Feb 28\nElaphēboliṓn: Mar 01–Mar 29\nMounukhiṓn: Mar 30–Apr 27\nThargēliṓn: Apr 28–May 27\nSkirophoriṓn: May 28–Jun 25\n"
    )


def test_year_summary(cal_2024):
    s = hem.year_summary(cal_2024[0])

    split_s1 = s[0].split("\n")
    assert (
        split_s1[0]
        == "2024/2025 will be an ordinary year of 355 days, ending on 2025-Jun-25. As an ordinary year there will be 12 months (1/2):"
    )
    assert split_s1[1] == ""
    assert split_s1[2] == "Hekatombaiṓn: Jul 06–Aug 04"
    assert split_s1[7] == "Posideiṓn: Dec 02–Dec 30"

    split_s2 = s[1].split("\n")
    assert split_s2[0] == "Months in 2024/2025 (2/2):"
    assert split_s2[2] == "Gamēliṓn: Dec 31–Jan 29"
    assert split_s2[7] == "Skirophoriṓn: May 28–Jun 25"
