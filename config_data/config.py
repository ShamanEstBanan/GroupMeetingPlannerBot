from dataclasses import dataclass

from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot


BOT_TOKEN = '7864102334:AAEtCE7RqNF7ZXU8RANqzGd0Xn9lCBRQvPc'
MONGO_ADDRESS = "mongodb://localhost:27017/"


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(
            # token=env('TOKEN')
            token=BOT_TOKEN,
        )
    )
