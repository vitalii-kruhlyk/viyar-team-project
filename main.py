from dotenv import load_dotenv

from interfaces.cli import CliBot

load_dotenv()


if __name__ == "__main__":
    CliBot().run()
