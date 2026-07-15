"""
tests/test_watchlist.py — CineLog

Tests for the watchlist service.
"""

import pytest
from app import create_app, db
from models import User, Film, WatchlistEntry
from services.watchlist_service import (
    add_to_watchlist,
    get_watchlist,
    AlreadyInWatchlistError,
    NotInWatchlistError,
    remove_from_watchlist,
)
from services.collection_service import FilmNotFoundError


@pytest.fixture
def app():
    """Create an isolated test app with an in-memory database."""
    app = create_app(config={
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_user(app):
    """A user to use in tests."""
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_film(app):
    """A film to use in tests."""
    with app.app_context():
        film = Film(title="Paddington 2", year=2017, genre="Comedy")
        db.session.add(film)
        db.session.commit()
        return film.id


# ── Nonexistent film ─────────────────────────────────────────────────────────

def test_add_to_watchlist_nonexistent_film_raises(app, sample_user):
    """
    Adding a film_id that doesn't exist in the database should raise
    FilmNotFoundError, not a database integrity error.
    """
    with app.app_context():
        fake_film_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(FilmNotFoundError):
            add_to_watchlist(user_id=sample_user, film_id=fake_film_id)


def test_remove_from_watchlist_removes_entry(app, sample_user, sample_film):
    with app.app_context():
        add_to_watchlist(user_id=sample_user, film_id=sample_film)
        result = remove_from_watchlist(user_id=sample_user, film_id=sample_film)
        assert result is True

        remaining = WatchlistEntry.query.filter_by(
            user_id=sample_user, film_id=sample_film
        ).first()
        assert remaining is None


def test_remove_from_watchlist_not_present_raises(app, sample_user, sample_film):
    with app.app_context():
        with pytest.raises(NotInWatchlistError):
            remove_from_watchlist(user_id=sample_user, film_id=sample_film)


def test_get_watchlist_empty_returns_empty_list(app, sample_user):
    """
    A user with no watchlist entries should receive an empty list, not an
    error or null-like value.
    """
    with app.app_context():
        result = get_watchlist(sample_user)
        assert result == []


def test_add_to_watchlist_respects_explicit_public_false(
    app, sample_user, sample_film
):
    """
    Callers should be able to explicitly set public=False instead of
    relying on the model's default.
    """
    with app.app_context():
        entry = add_to_watchlist(
            user_id=sample_user,
            film_id=sample_film,
            public=False,
        )
        assert entry.public is False
