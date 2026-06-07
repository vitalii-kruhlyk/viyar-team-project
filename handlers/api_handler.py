import requests
from collections.abc import Callable

from handlers.decorators import input_error

class WeatherService:
    commands: dict[str, Callable[[list[str]], tuple[str, bool]]]

    def __init__(self) -> None:
        self.commands = {
            "weather": self.get_weather
        }
        self.descriptions = {
            "weather": "Receives weather data for the city : weather <City>"
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
            "&hourly=precipitation_probability"
        )

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            response.raise_for_status()

            data = response.json()

            current = data["current"]
            probability = data["hourly"]["precipitation_probability"][0]

            return (f"Temperature: {current['temperature_2m']}°C\nWind speed: {current['wind_speed_10m']} km/h"
                    f"\nProbability of rain: {probability}%"), False

        return "Unable to retrieve city data", False

    @staticmethod
    @input_error
    def get_coordinates(city: str) -> list[str]|None:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search"f"?name={city}&count=1"
        )

        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()["results"][0]

            return [result.get("latitude"), result.get("longitude")]

        return None

class CurrencyService:
    commands: dict[str, Callable[[list[str]], tuple[str, bool]]]

    def __init__(self) -> None:
        self.commands = {
            "currencies": self.get_currency_rate
        }
        self.descriptions = {
            "currencies": "Gets the exchange rate for today"
        }
        self.currencies = ["USD", "EUR", "PLN"]

    @input_error
    def get_currency_rate(self, args: list[str]) -> tuple[str, bool]:

        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        response = requests.get(url)
        if response.status_code == 200:

            rates = response.json()
            currency_info = ""
            for currency in self.currencies:

                rate = next(
                    (item for item in rates if item["cc"] == currency),
                    None
                    )

                if rate is None:
                    return f"Currency {currency} not found", False

                currency_info =  f"{rate['cc']}\n"
                f"Rate: {rate['rate']} UAH\n"
                f"Date: {rate['exchangedate']}"

            return currency_info, False

        return "Unable to retrieve currency data", False