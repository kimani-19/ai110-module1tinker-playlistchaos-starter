from typing import Dict, List, Optional, Tuple  # import typing helpers for annotations

Song = Dict[str, object]  # alias: a Song is a dict with string keys and arbitrary values
PlaylistMap = Dict[str, List[Song]]  # alias: map playlist name -> list of Songs

DEFAULT_PROFILE = {
    "name": "Default",  # default profile name
    "hype_min_energy": 7,  # energy threshold to consider a song "Hype"
    "chill_max_energy": 3,  # energy threshold to consider a song "Chill"
    "favorite_genre": "rock",  # default favorite genre
    "include_mixed": True,  # flag to include mixed songs (not used everywhere)
}


def normalize_title(title: str) -> str:
    """Normalize a song title for comparisons."""
    if not isinstance(title, str):  # ensure input is a string
        return ""  # return empty string for non-string inputs
    return title.strip()  # trim whitespace from both ends


def normalize_artist(artist: str) -> str:
    """Normalize an artist name for comparisons."""
    if not artist:  # empty or falsy artist
        return ""  # return empty string
    return artist.strip().lower()  # trim and lowercase for consistent comparison


def normalize_genre(genre: str) -> str:
    """Normalize a genre name for comparisons."""
    return genre.lower().strip()  # lowercase then trim whitespace


def normalize_song(raw: Song) -> Song:
    """Return a normalized song dict with expected keys."""
    title = normalize_title(str(raw.get("title", "")))  # get and normalize title
    artist = normalize_artist(str(raw.get("artist", "")))  # get and normalize artist
    genre = normalize_genre(str(raw.get("genre", "")))  # get and normalize genre
    energy = raw.get("energy", 0)  # default energy to 0 if missing

    if isinstance(energy, str):  # if energy provided as string
        try:
            energy = int(energy)  # try to convert to int
        except ValueError:
            energy = 0  # fallback to 0 on conversion failure

    tags = raw.get("tags", [])  # get tags or default to empty list
    if isinstance(tags, str):  # if tags is a single string
        tags = [tags]  # convert into a list containing that string

    return {
        "title": title,  # normalized title
        "artist": artist,  # normalized artist
        "genre": genre,  # normalized genre
        "energy": energy,  # numeric energy value
        "tags": tags,  # normalized tags list
    }


def classify_song(song: Song, profile: Dict[str, object]) -> str:
    """Return a mood label given a song and user profile."""
    energy = song.get("energy", 0)  # read energy, default 0
    genre = song.get("genre", "")  # read genre, default empty
    title = song.get("title", "")  # read title, default empty

    hype_min_energy = profile.get("hype_min_energy", 7)  # profile's hype energy threshold
    chill_max_energy = profile.get("chill_max_energy", 3)  # profile's chill energy threshold
    favorite_genre = profile.get("favorite_genre", "")  # profile's favorite genre

    hype_keywords = ["rock", "punk", "party"]  # keywords indicating hype
    chill_keywords = ["lofi", "ambient", "sleep"]  # keywords indicating chill

    is_hype_keyword = any(k in genre for k in hype_keywords)  # any hype keyword in genre

    # FIX 4: Check genre (not title) for chill keywords.
    is_chill_keyword = any(k in genre for k in chill_keywords)  # any chill keyword in genre

    if genre == favorite_genre or energy >= hype_min_energy or is_hype_keyword:
        return "Hype"  # classify as Hype if any hype condition met
    if energy <= chill_max_energy or is_chill_keyword:
        return "Chill"  # classify as Chill if any chill condition met
    return "Mixed"  # otherwise Mixed


def build_playlists(songs: List[Song], profile: Dict[str, object]) -> PlaylistMap:
    """Group songs into playlists based on mood and profile."""
    playlists: PlaylistMap = {
        "Hype": [],  # list for hype songs
        "Chill": [],  # list for chill songs
        "Mixed": [],  # list for mixed songs
    }

    for song in songs:  # iterate over input songs
        normalized = normalize_song(song)  # normalize the song data
        mood = classify_song(normalized, profile)  # determine mood
        normalized["mood"] = mood  # annotate normalized song with mood
        playlists[mood].append(normalized)  # append to appropriate playlist

    return playlists  # return the populated playlists map


def merge_playlists(a: PlaylistMap, b: PlaylistMap) -> PlaylistMap:
    """Merge two playlist maps into a new map."""
    merged: PlaylistMap = {}  # start with an empty map
    for key in set(list(a.keys()) + list(b.keys())):  # union of keys from both maps
        merged[key] = a.get(key, [])  # take list from a or empty
        merged[key].extend(b.get(key, []))  # extend with list from b
    return merged  # return merged result


def compute_playlist_stats(playlists: PlaylistMap) -> Dict[str, object]:
    """Compute statistics across all playlists."""
    all_songs: List[Song] = []  # flattened list of all songs
    for songs in playlists.values():
        all_songs.extend(songs)  # extend with each playlist's songs

    hype = playlists.get("Hype", [])  # get hype list
    chill = playlists.get("Chill", [])  # get chill list
    mixed = playlists.get("Mixed", [])  # get mixed list

    # FIX 1: Use total number of songs for ratios and compute average energy across all songs.
    total_songs = len(all_songs)
    hype_ratio = len(hype) / total_songs if total_songs > 0 else 0.0

    avg_energy = 0.0
    if total_songs > 0:
        total_energy = sum(song.get("energy", 0) for song in all_songs)
        avg_energy = total_energy / total_songs

    top_artist, top_count = most_common_artist(all_songs)  # find most common artist

    return {
        "total_songs": len(all_songs),  # count of all songs
        "hype_count": len(hype),  # count of hype songs
        "chill_count": len(chill),  # count of chill songs
        "mixed_count": len(mixed),  # count of mixed songs
        "hype_ratio": hype_ratio,  # computed hype ratio
        "avg_energy": avg_energy,  # computed average energy
        "top_artist": top_artist,  # most common artist
        "top_artist_count": top_count,  # count for top artist
    }


def most_common_artist(songs: List[Song]) -> Tuple[str, int]:
    """Return the most common artist and count."""
    counts: Dict[str, int] = {}  # frequency map artist -> count
    for song in songs:
        artist = str(song.get("artist", ""))  # read artist as string
        if not artist:
            continue  # skip empty artist values
        counts[artist] = counts.get(artist, 0) + 1  # increment count

    if not counts:  # if no artists found
        return "", 0  # return empty result

    items = sorted(counts.items(), key=lambda item: item[1], reverse=True)  # sort by count desc
    return items[0]  # return top (artist, count)


def search_songs(
    songs: List[Song],
    query: str,
    field: str = "artist",
) -> List[Song]:
    """Return songs matching the query on a given field."""
    if not query:  # empty query -> no filtering
        return songs

    q = query.lower().strip()  # normalize query
    filtered: List[Song] = []  # prepare result list

    for song in songs:
        value = str(song.get(field, "")).lower()  # read field value and lowercase
        # FIX 2: membership test was reversed — check whether query is contained in the field value
        if q and q in value:
            filtered.append(song)  # append matching song

    return filtered  # return filtered results


def lucky_pick(
    playlists: PlaylistMap,
    mode: str = "any",
) -> Optional[Song]:
    """Pick a song from the playlists according to mode."""
    if mode == "hype":
        songs = playlists.get("Hype", [])  # choose hype songs
    elif mode == "chill":
        songs = playlists.get("Chill", [])  # choose chill songs
    else:
        songs = playlists.get("Hype", []) + playlists.get("Chill", [])  # combine both

    return random_choice_or_none(songs)  # delegate to random picker


def random_choice_or_none(songs: List[Song]) -> Optional[Song]:
    """Return a random song or None."""
    import random  # import local to keep scope small
    # FIX 3: return None for empty lists instead of raising IndexError
    if not songs:
        return None
    return random.choice(songs)  # pick a random item


def history_summary(history: List[Song]) -> Dict[str, int]:
    """Return a summary of moods seen in the history."""
    counts = {"Hype": 0, "Chill": 0, "Mixed": 0}  # initialize counters
    for song in history:
        mood = song.get("mood", "Mixed")  # read mood, default Mixed
        if mood not in counts:
            counts["Mixed"] += 1  # unknown moods counted as Mixed
        else:
            counts[mood] += 1  # increment proper mood counter
    return counts  # return the summary
