from fastapi import FastAPI
from pydantic import BaseModel

from src.spotify import get_tracks

app = FastAPI()


class InputModel(BaseModel):
    client_id: str
    client_secret: str


@app.post("/tracks/")
def get_spotify_track(input_model: InputModel):
    try:
        track_vibes = get_tracks(
            client_id=input_model.client_id,
            client_secret=input_model.client_secret,
        )
    except Exception as e:
        return {"error": str(e)}
    return track_vibes


@app.post("/square/")
def square(x: int):
    return {"square": x**2}
