import requests
from collections.abc import Callable

from handlers.decorators import input_error

class APIHendler:
    commands: dict[str, Callable[[list[str]], tuple[str, bool]]]

    def __init__(self) -> None:
        self.commands = {
            "weather": self.get_weather
        }

    @input_error
    def get_weather(self, args: list[str]) -> tuple[str, bool]:
        if len(args) != 1:
            raise ValueError("Usage: weather <City>")

        city = args[0]

        lat, lng = self.get_coordinates(city)
        if lng is None:
            return "Unable to retrieve city data", False

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}"
            f"&longitude={lng}"
            "&current=temperature_2m,wind_speed_10m"
        )

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            response.raise_for_status()

            data = response.json()

            current = data["current"]

            return f"Temperature: {current['temperature_2m']}°C\nWind speed: {current['wind_speed_10m']} km/h", False

        return "Unable to retrieve city data", False

    @staticmethod
    @input_error
    def get_coordinates(city: str) -> list[str]|None:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={city}&count=1"
        )

        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()["results"][0]

            return [result.get("lat"), result.get("lng")]

        return None