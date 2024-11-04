from aiogram import Router
from aiogram.filters import Command, CommandStart

from config_data.config import Config, load_config
from aiogram.types import Message

config: Config = load_config()

router: Router = Router()

@router.message(CommandStart())
async def send_welcome(message: Message) -> None:
    await message.reply("Привет! Я помогу вам выбрать лучшее время для встречи!\n"
                        "Команда /help поможет узнать доступные команды")


@router.message(Command('help'))
async def send_welcome(message: Message) -> None:
    await message.reply("Команды:\n"
                        "/start Начало работы бота\n"
                        "/help Узнать справочную информацию\n"
                        "/meetings Посмотреть список встреч или создать новую")

