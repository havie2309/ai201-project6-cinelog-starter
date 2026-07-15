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

**My position:** I agree that watchlists should default to newest-first
order using `date_added`, while alphabetical sorting could be offered
later as an optional view.

**Reasoning:** A watchlist is more similar to a queue of films a user
intends to watch than a permanent reference catalog. Users are therefore
likely to revisit it to remember what recently caught their interest or
decide what to watch next. When a watchlist grows to dozens of films, the
user may not remember the exact title of every item, but they are more
likely to remember that they added a film recently. Sorting by
`date_added` descending keeps those recent decisions visible and prevents
newly added films from being buried elsewhere in the list based only on
their title.

The current data model also supports this interpretation. Each
`WatchlistEntry` already stores a `date_added` timestamp, while the
watchlist feature does not currently include a search or filtering
mechanism designed for catalog-style lookup. That makes recency the
stronger default for the behavior the existing implementation can support
well.

Alphabetical ordering is still useful when a user wants to check whether
a specific film is already saved, especially for a large watchlist.
However, that behavior would be better supported by a search feature or
an optional alphabetical sort than by making alphabetical order the
default.

**Engagement with reviewer's point:** I agree with the reviewer's point
that most users are likely to want recently added films first because
that ordering matches the primary use of a watchlist as an active queue.
I would change `get_watchlist()` from `.order_by(Film.title.asc())` to
`.order_by(WatchlistEntry.date_added.desc())`, while keeping the existing
join with `Film` for building the response data. An optional alphabetical
sort could be added in a future enhancement, but it is outside the scope
of this PR.

## Comment 6 — Rebase

**What conflicted:** While `feature/watchlist` was open, `main` merged a
refactor migrating `Film.id` (and related foreign keys) from `Integer` to
UUID strings. My branch's `models.py` still defined `Film.id` as an
auto-incrementing integer, and `WatchlistEntry.film_id` referenced that
integer type. Because git could not detect a textual conflict between the
two versions of `models.py` (the class ordering didn't overlap directly),
the rebase completed without flagging a conflict — but it silently
dropped the `WatchlistEntry` model entirely, since the post-refactor
`main` version of `models.py` never had it.

**How I resolved it:** I manually re-added the `WatchlistEntry` class to
`models.py` after the rebase completed, using `db.String(36)` for
`film_id` to match the new UUID foreign key on `Film.id`, instead of the
old `db.Integer`. I also updated the docstring in
`add_to_watchlist()` (in `services/watchlist_service.py`) to reflect that
`film_id` is now a UUID string, and updated the fake film ID used in
`test_add_to_watchlist_nonexistent_film_raises` from an integer
placeholder to a UUID-formatted string, matching the convention used in
`test_collection.py`.

**How I verified no conflict remains:** Ran `pytest tests/ -v` after the
fix — all 5 tests passed, including the previously-broken
`test_watchlist.py` (which had failed to even import `WatchlistEntry`
before the fix). Also ran `git log --oneline --graph` to confirm the
branch history remains linear with no merge commits introduced by me.

## Stretch — remove_from_watchlist()
**What I did:** Implemented `remove_from_watchlist(user_id, film_id)` in
`services/watchlist_service.py`, following the same pattern as
`remove_from_collection()` — checks for an existing entry via
`filter_by(user_id, film_id).first()`, raises a new `NotInWatchlistError`
if not found, otherwise deletes and commits. Added a corresponding
`DELETE /watchlist/<user_id>/remove` route.
**Tests:** Added two tests — one confirming successful removal, one
confirming `NotInWatchlistError` is raised when the film isn't on the
watchlist.

## Stretch — Second test
**What I did:** Added `test_get_watchlist_empty_returns_empty_list`, which
verifies that `get_watchlist()` returns an empty list `[]` for a user with
no watchlist entries, rather than raising an error or returning `None`.
**Why I chose this case:** Every other test exercises a watchlist with at
least one entry. An empty watchlist is the very first state a real user
would encounter, and it's an easy case to get subtly wrong (e.g. returning
`None` if the query result isn't handled, or the endpoint crashing on an
empty list when building a response) — so it's worth covering explicitly
even though the reviewer didn't request it.

## Stretch — Visibility toggle
**What I did:** Added a `public` parameter to `add_to_watchlist(user_id,
film_id, public=True)`, so callers can explicitly set visibility instead
of always relying on the `WatchlistEntry` model's default. The
`POST /watchlist/<user_id>/add` endpoint now reads an optional `public`
field from the request body (defaulting to `True` if omitted) and passes
it through. This directly addresses the follow-up gap I noted in my
Comment 4 response — previously there was no way for a caller to opt out
of the public default.
**Tests:** Added a test confirming that passing `public=False` explicitly
is respected on the created entry.

## PR Description
<!-- Written at the end — feature overview, design decisions, manual testing steps -->
