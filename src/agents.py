"""We want to parse spotify data and create a sentence that describes the user's mood."""

import math
import os
from ast import literal_eval
from collections import Counter

import numpy as np
import pandas as pd
import requests
import typer
from dotenv import load_dotenv
from mirascope import tags
from mirascope.openai import OpenAICall, OpenAICallParams
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


@tags(["version:0002"])
class MusicAnnotator(OpenAICall):
    prompt_template = """
    SYSTEM:
    You are a quantitative mood analyzer. You are going to analyze the mood\n
    of a user based on their Spotify data in accordance to the affective circumplex model.

    Represent the response as a list of 8 words representing emotions properly syntaxed for Python\n
    and nest this inside a key called "words" in a dictionary that returns the input valence (float)\n
    energy (float), danceability (float), and number of tracks (int) for the user as a dictionary.

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


@tags(["version:0002"])
class MoodExaminer(OpenAICall):
    prompt_template = """
    SYSTEM:
    You are a quantitative mood analyzer. You are going to analyze the mood\n
    of a user based on a user chat in accordance to the affective circumplex model.\n
    Represent the mood from the user chat as a list of 8 words properly syntaxed for Python.\n

    USER:
    {user_chat}
    """
    user_chat: str
    call_params = OpenAICallParams(model="gpt-4", temperature=0.4)


@tags(["version:0001"])
class ContrastiveAgent(OpenAICall):
    prompt_template = """
    SYSTEM:
    You are really good at contrasting lists of text. You are going to contrast the\n
    extracted 8 words from the user chat and the 8 words from the Spotify data.\n
    Then you will answer the question with either "Yes" if the two lists are similar\n
    or "No" if the two lists are different.

    The words are chosen from the list of words in the affective circumplex model.\n

    USER:
    User Chat List: {user_chat}
    Spotify Chat List: {spotify_chat}
    """
    user_chat: list
    spotify_chat: list
    call_params = OpenAICallParams(model="gpt-4", temperature=0.4)


def counter_cosine_similarity(c1, c2):
    terms = set(c1).union(c2)
    dotprod = sum(c1.get(k, 0) * c2.get(k, 0) for k in terms)
    magA = math.sqrt(sum(c1.get(k, 0) ** 2 for k in terms))
    magB = math.sqrt(sum(c2.get(k, 0) ** 2 for k in terms))
    return dotprod / (magA * magB)


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
    list_of_user_mood = literal_eval(user_mood)

    # Create a dictionary with the mood data
    data = {"Spotify Playlist Mood": spotify_mood["words"], "User Chat Mood": list_of_user_mood}

    # Print the DataFrame
    print(pd.DataFrame(data).to_markdown())

    # Compare the two moods
    contrastive_agent_response = ContrastiveAgent(
        user_chat=list_of_user_mood, spotify_chat=spotify_mood["words"]
    ).call()
    contrastive_agent_response = contrastive_agent_response.dump()["output"]["choices"][0][
        "message"
    ]["content"]

    if "Yes" in contrastive_agent_response:
        print(
            "\n\n[green][bold]Contrastive agent feels the two sentiments are similar.[/bold][/green]"
        )
    else:
        print("\n\n[red]Contrastive agent feels the two sentiments are different.[/red]")

    # cosine = counter_cosine_similarity(Counter(list_of_user_mood), Counter(spotify_mood["words"]))
    # print(f"\n\n[red]Cosine Similarity:[/red] {cosine:.2f}")
    # if cosine > 0.5:
    #     print("[green][bold]The two sentiments are similar.[/bold][/green]")
    # else:
    #     print("[red]The two sentiments are different.[/red]")


if __name__ == "__main__":
    app()
