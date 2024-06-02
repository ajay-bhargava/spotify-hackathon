import datetime

import spotipy
from rich import print
from spotipy.oauth2 import SpotifyOAuth


def get_tracks(
    client_id: str,
    client_secret: str,
):
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri="http://localhost:3000",
            scope=["user-read-recently-played", "user-library-read"],
            open_browser=False,
        )
    )
    # Get the current date and time
    now = datetime.datetime.now()

    # Set the time to 12am
    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Get the POSIX timestamp of the start time
    start = int(start_time.timestamp() * 1000)
    results = sp.current_user_recently_played(after=start)

    parsing = []
    for idx, item in enumerate(results["items"]):
        parsing.append(
            {
                "spotify_identifier": item["track"]["id"],
                "track_name": item["track"]["name"],
                "artist_name": item["track"]["artists"][0]["name"],
            }
        )

    identifiers = [item["spotify_identifier"] for item in parsing]
    print(parsing)
    track_vibes = sp.audio_features(identifiers)
    return track_vibes
