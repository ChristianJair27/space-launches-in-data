"""Consistency checks on the parsed GCAT data (run `python -m worldspace` once first)."""

import pytest

from worldspace import RAW, analysis

pytestmark = pytest.mark.skipif(not (RAW / "launch.tsv").exists(),
                                reason="GCAT files not downloaded; run python -m worldspace")


@pytest.fixture(scope="module")
def tables():
    return analysis.build()


def test_only_real_launches(tables):
    L = tables["launches"]
    assert set(L.launch_code.str[0]) <= {"O", "D"}
    assert set(L.launch_code.str[1]) <= {"S", "F"}      # no pad explosions (E) or aborts (A)
    assert L.tag.is_unique


def test_sputnik_first(tables):
    L = tables["launches"]
    first = L.sort_values("jd").iloc[0]
    assert first.tag.startswith("1957 ALP") and first.success


def test_groups_cover_everything(tables):
    by_year = tables["by_year"]
    assert by_year.to_numpy().sum() == len(tables["launches"])


def test_booster_flight_numbers_increment_by_one(tables):
    b = tables["boosters"]
    steps = b.groupby("booster").flight_no.diff().dropna()
    assert (steps == 1).all()
    assert (b.turnaround_days.dropna() > 0).all()


def test_cargo_mass_never_negative(tables):
    assert (tables["launches"].cargo_t >= 0).all()
