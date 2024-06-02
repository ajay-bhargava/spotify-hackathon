"""We want to parse spotify data and create a sentence that describes the user's mood."""

import os
from ast import literal_eval
from typing import Any, Type

import numpy as np
import requests
import typer
from dotenv import load_dotenv
from mirascope import tags
from mirascope.openai import OpenAICall, OpenAICallParams, OpenAIExtractor
from pydantic import BaseModel
from rich import print

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

app = typer.Typer()


def get_spotify_data() -> dict:
    """retrieve the user's spotify data from an API endpoint."""
    url = "https://7281-108-41-92-245.ngrok-free.app/tracks/"
    payload = {
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    list_of_tracks = response.json()

    track_data = {
        "valence": np.mean([track["valence"] for track in list_of_tracks]),
        "energy": np.mean([track["energy"] for track in list_of_tracks]),
        "danceability": np.mean([track["danceability"] for track in list_of_tracks]),
        "number_of_tracks": len(list_of_tracks),
    }
    return track_data


@tags(["version:0001"])
class MusicAnnotator(OpenAICall):
    prompt_template = """
    SYSTEM:
    You are a quantitative mood analyzer. You are going to analyze the mood\n
    of a user based on their Spotify data in accordance to the affective circumplex model.
    You are given the following understanding of energy and valence:

    # Energy: Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and\n
    # activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has\n
    # high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to\n 
    # this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy.

    # Valence: Valence is a measure from 0.0 to 1.0 and describes the musical positiveness conveyed by a\n
    # track. Tracks with high valence sound more positive (e.g., happy, cheerful, euphoric), while tracks\n
    # with low valence sound more negative (e.g., sad, depressed, angry).

    Represent the response as a list of 8 words representing emotions properly syntaxed for Python and nest this inside a\n 
    key called "words" in a dictionary that returns the input valence (float), energy (float),\n
    danceability (float), and number of tracks (int) for the user as a dictionary.

    USER:
    {spotify_data}
    """
    spotify_data: dict
    call_params = OpenAICallParams(model="gpt-4", temperature=0.4)


def get_mood():
    analyzer = MusicAnnotator(spotify_data=get_spotify_data())
    analysis = analyzer.call()
    interpretation = literal_eval(analysis.dump()["output"]["choices"][0]["message"]["content"])
    try:
        assert isinstance(interpretation, dict), "interpretation is not a dictionary"
    except AssertionError as e:
        print(f"[red]{e}[/red]", type(interpretation))

    return interpretation


@tags(["version:0001"])
class MoodExaminer(OpenAICall):
    prompt_template = """
    SYSTEM:
    You are a quantitative mood analyzer. You are going to analyze the mood\n
    of a user based on a user chat in accordance to the affective circumplex model.\n

    Energy: Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and\n
    activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has\n
    high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to\n 
    this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy.

    Valence: Valence is a measure from 0.0 to 1.0 and describes the musical positiveness conveyed by a\n
    track. Tracks with high valence sound more positive (e.g., happy, cheerful, euphoric), while tracks\n
    with low valence sound more negative (e.g., sad, depressed, angry).

    Represent the response as a list of 8 words properly syntaxed for Python as a dictionary with key\n
    value pairs.

    USER:
    {user_chat}
    """
    user_chat: str
    call_params = OpenAICallParams(model="gpt-4", temperature=0.4)


@app.command()
def compare_and_contrast():
    """Perform a comparison of the user chat against the Spotify data from the get_mood function."""
    # Get user chat.
    user_chat = typer.prompt("What text do you plan on sending? Enter it here")

    # Get mood from Spotify data.
    spotify_mood = get_mood()

    # Get mood from user chat.
    user_mood = MoodExaminer(user_chat=user_chat).call()
    user_mood = user_mood.dump()["output"]["choices"][0]["message"]["content"]

    print(f"Spotify Mood: {spotify_mood}, User Mood: {user_mood}")


if __name__ == "__main__":
    app()
