# Installation

To run a copy of this server first install `ngrok`. 

```bash
brew install --cask ngrok
```

then spin up the `FastAPI` server

```bash
fastapi dev src/api.py
```

then run `ngrok` to expose the server to the internet

```bash
ngrok http 8000
```

# Testing

You can test the server on a Google CoLab notebook [here](https://colab.research.google.com/drive/1g35zeVQcKyj0nGk_GUFplw93yPakdezp?authuser=0#scrollTo=F8NIAwtKgmJ1). 

