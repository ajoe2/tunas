"""
Tests for database package
"""

import database


def test_database_basic():
    d = database.Database()
    assert d.get_clubs() == []
    assert d.get_meet_results() == []
    assert d.get_meets() == []
    assert d.get_swimmers() == []
