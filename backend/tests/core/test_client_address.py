"""Originating client address rule and parser (SR-042 AC 1 to AC 3, TS-016 TC-016.1, TC-016.2)."""

import pytest

from app.core.client_address import originating_address, parse_trusted_proxies

PROXY = parse_trusted_proxies("10.0.0.2")
TWO = parse_trusted_proxies("10.0.0.2, 10.0.0.3")


# --- SR-042 AC 1: right-most untrusted entry from a trusted peer -------------------------------


def test_trusted_peer_takes_the_forwarded_client() -> None:
    assert originating_address("10.0.0.2", "203.0.113.7", PROXY) == "203.0.113.7"


def test_chain_with_both_proxies_trusted_gives_the_client() -> None:
    assert originating_address("10.0.0.2", "203.0.113.7, 10.0.0.3", TWO) == "203.0.113.7"


def test_all_entries_trusted_gives_the_left_most() -> None:
    assert originating_address("10.0.0.2", "10.0.0.3, 10.0.0.2", TWO) == "10.0.0.3"


def test_forged_leading_entry_is_ignored_right_most_untrusted_wins() -> None:
    assert originating_address("10.0.0.2", "1.2.3.4, 203.0.113.7", PROXY) == "203.0.113.7"


def test_cidr_entry_trusts_the_block() -> None:
    trusted = parse_trusted_proxies("10.0.0.0/24")
    assert originating_address("10.0.0.9", "203.0.113.7, 10.0.0.5", trusted) == "203.0.113.7"


def test_trusted_peer_without_header_gives_the_peer() -> None:
    assert originating_address("10.0.0.2", None, PROXY) == "10.0.0.2"
    assert originating_address("10.0.0.2", "", PROXY) == "10.0.0.2"


def test_ipv6_client_through_ipv6_proxy() -> None:
    trusted = parse_trusted_proxies("fd00::2")
    assert originating_address("fd00::2", "2001:db8::1", trusted) == "2001:db8::1"


def test_ipv6_is_normalised_and_families_do_not_cross_match() -> None:
    trusted = parse_trusted_proxies("10.0.0.2")
    assert originating_address("10.0.0.2", "2001:DB8:0:0::1", trusted) == "2001:db8::1"


# --- SR-042 AC 2: header from an untrusted peer is ignored -------------------------------------


def test_untrusted_peer_header_is_ignored() -> None:
    assert originating_address("198.51.100.9", "203.0.113.7", PROXY) == "198.51.100.9"


# --- SR-042 AC 3: empty setting trusts nothing -------------------------------------------------


def test_empty_setting_trusts_no_peer() -> None:
    assert parse_trusted_proxies("") == ()
    assert parse_trusted_proxies(" , ") == ()
    assert originating_address("10.0.0.2", "203.0.113.7", ()) == "10.0.0.2"


def test_no_peer_gives_none() -> None:
    assert originating_address(None, "203.0.113.7", PROXY) is None


# --- malformed input is skipped, never trusted -------------------------------------------------


def test_malformed_entries_are_skipped() -> None:
    assert originating_address("10.0.0.2", "203.0.113.7, garbage, ", PROXY) == "203.0.113.7"
    assert originating_address("10.0.0.2", "unknown, 300.1.1.1", PROXY) == "10.0.0.2"


def test_non_ip_peer_is_returned_untrusted() -> None:
    assert originating_address("testclient", "203.0.113.7", PROXY) == "testclient"


# --- parser ------------------------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["not-an-ip", "10.0.0.2, 10.0.0.999", "10.0.0.2/99", "10.0.0.1/24"])
def test_invalid_setting_raises_naming_the_entry(bad: str) -> None:
    with pytest.raises(ValueError, match="TRUSTED_PROXIES entry"):
        parse_trusted_proxies(bad)


def test_invalid_entry_is_named() -> None:
    with pytest.raises(ValueError, match="10.0.0.999"):
        parse_trusted_proxies("10.0.0.2, 10.0.0.999")
