"""Capability tests — the security model, which everything else rests on."""

from __future__ import annotations

import pytest

from ooos.capability import ALL, RW, Rights, Capability, format_rights, parse_rights
from ooos.errors import NotPermitted


def test_parse_rights():
    assert parse_rights("rw") == Rights.READ | Rights.WRITE
    assert parse_rights("rwxgd") == ALL
    assert parse_rights("") == Rights.NONE
    assert parse_rights("r-w") == Rights.READ | Rights.WRITE


def test_parse_rights_rejects_typos():
    with pytest.raises(ValueError):
        parse_rights("rwz")


def test_format_roundtrip():
    rights = Rights.READ | Rights.WRITE
    assert parse_rights(format_rights(rights).replace("-", "")) == rights


def test_require_passes_when_rights_are_present():
    cap = Capability(oid=1, rights=RW)
    cap.require(Rights.READ)
    cap.require(RW)


def test_require_raises_when_a_right_is_missing():
    cap = Capability(oid=1, rights=Rights.READ)
    cap.require(Rights.READ)
    with pytest.raises(NotPermitted):
        cap.require(Rights.WRITE)


def test_restrict_can_only_narrow():
    cap = Capability(oid=1, rights=RW)
    narrowed = cap.restrict(Rights.READ)
    assert narrowed.rights == Rights.READ
    with pytest.raises(NotPermitted):
        narrowed.require(Rights.WRITE)


def test_restrict_never_widens():
    cap = Capability(oid=1, rights=Rights.READ)
    assert cap.restrict(RW).rights == Rights.READ


def test_capabilities_are_value_identical_and_hashable():
    a = Capability(oid=7, rights=RW)
    b = Capability(oid=7, rights=RW)
    assert a == b
    assert len({a, b}) == 1


def test_capabilities_are_immutable():
    cap = Capability(oid=7, rights=RW)
    with pytest.raises(Exception):
        cap.oid = 8  # type: ignore[misc]
