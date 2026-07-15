# PR Response Doc — CineLog Watchlist Feature

## AI Usage
- Asked Claude to critique my Comment 4 draft. Revised it to acknowledge
  that the visibility toggle does not yet exist in the codebase, compare
  watchlist privacy with collection data, and explain why the social value
  of public film interests outweighs the relatively limited privacy risk
  in this context.

## Comment 1 — Rename
**What I did:** Renamed `save_to_watchlist()` to `add_to_watchlist()` in
`services/watchlist_service.py` to match the `verb_to_noun` naming convention
used by `add_to_collection()`. Updated the one call site in
`routes/watchlist/watchlist.py`.

**How I verified:** Ran `grep -rn "save_to_watchlist" .` across the repo to
confirm no remaining references to the old name.

## Comment 2 — Deduplication

**What I did:** Added a check in `add_to_watchlist()` that queries
`WatchlistEntry.query.filter_by(user_id=user_id, film_id=film_id).first()`
before creating a new entry. If a match is found, raises a new
`AlreadyInWatchlistError` instead of silently creating a duplicate.

**How I verified:** Mirrored the exact pattern used in
`add_to_collection()` in `collection_service.py`, which does the same
existence check before raising `AlreadyInCollectionError`. I also reviewed
the updated service logic to confirm the duplicate check happens before
the new watchlist entry is created, and ran the full test suite to confirm
no regressions.

## Comment 3 — Missing test

**What I did:** Created `tests/test_watchlist.py` with
`test_add_to_watchlist_nonexistent_film_raises`, modeled directly on
`test_add_to_collection_nonexistent_film_raises` in `test_collection.py` —
same fixture structure (`app`, `sample_user`), same assertion style
(`pytest.raises(FilmNotFoundError)`).

**How I verified:** Ran `pytest tests/test_watchlist.py -v` to confirm the
test passes, then `pytest tests/ -v` to confirm no other tests broke.

## Comment 4 — Default visibility

**My position:** I would keep `public=True` as the default for watchlist
entries, but I would document the lack of visibility controls as a
follow-up gap rather than implying that users can already change this
setting.

**Reasoning:** CineLog is a community film-tracking platform, and public
watchlists support specific social behaviors: friends can discover films
through each other, recommend similar titles, or plan to watch something
together. This value is different from a collection, which records films
a user has already watched. A watchlist shows future interest and intent,
so it can be somewhat more personal than viewing history; the presence of
a `public` field on `WatchlistEntry`, while `CollectionEntry` has no
equivalent field, suggests that this distinction was intentional. However,
film preferences are generally lower-risk than highly sensitive information
such as health, financial, or location data. In this context, I believe
the loss of the feature's main community and discovery value from making
every watchlist private by default would outweigh the typical privacy
harm of exposing film interests.

**Tradeoff acknowledged:** A `public=False` default would be safer for
users who add personal, sensitive, or potentially embarrassing films and
do not realize that default settings are persistent. That is a meaningful
concern, especially because the current implementation does not accept a
`public` argument in `add_to_watchlist()` and does not provide an endpoint
for changing visibility later. I would still keep `public=True` for this
PR because it aligns with CineLog's community-focused purpose, but I would
explicitly record a visibility toggle and clear visibility indicator as
necessary follow-up work. Without that follow-up, users currently have no
practical control over the privacy choice represented by the model.

## Comment 5 — Sort order
**My position:**
**Reasoning:**
**Engagement with reviewer's point:**

## Comment 6 — Rebase
**What conflicted:**
**How I resolved it:**
**How I verified no conflict remains:**

## PR Description
<!-- Written at the end — feature overview, design decisions, manual testing steps -->