import requests
from requests.exceptions import RequestException

from handlers.decorators import input_error


class WeatherService:
    @input_error
    def get_weather(self, flags: dict[str, str]) -> tuple[str, bool]:
        if "-city" not in flags:
            raise ValueError("Usage: show --weather -city <City>")

        city = flags["-city"]

        coordinates = self.get_coordinates(city)

        if coordinates is None:
            return "Unable to retrieve city data", False

        lat, lng = coordinates

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}"
            f"&longitude={lng}"
            "&current=temperature_2m,wind_speed_10m"
            "&hourly=precipitation_probability"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            current = data["current"]
            probability = data["hourly"]["precipitation_probability"][0]

            return (
                f"Temperature: {current['temperature_2m']}°C\nWind speed: {current['wind_speed_10m']} km/h"
                f"\nProbability of rain: {probability}%"
            ), False
        except RequestException:
            return "Unable to retrieve weather data", False

    @staticmethod
    @input_error
    def get_coordinates(city: str) -> tuple[float, float] | None:
        url = "https://geocoding-api.open-meteo.com/v1/search"

        try:
            response = requests.get(url, params={"name": city, "count": 1}, timeout=10)
            response.raise_for_status()

            results = response.json().get("results")
            if not results:
                return None
            result = results[0]

            return result["latitude"], result["longitude"]
        except RequestException:
            return None


class CurrencyService:
    def __init__(self) -> None:
        self.currencies = ["USD", "EUR", "PLN"]

    @input_error
    def get_currency_rate(self, flags: dict[str, str]) -> tuple[str, bool]:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            rates = response.json()
            currency_info = []

            for currency in self.currencies:
                rate = next((item for item in rates if item["cc"] == currency), None)

                if rate is None:
                    currency_info.append(f"{currency}: not found")
                    continue

                currency_info.append(f"{rate['cc']}: " f"{rate['rate']} UAH " f"({rate['exchangedate']})")

            return "\n".join(currency_info), False
        except RequestException:
            return "Unable to retrieve currency data", False
