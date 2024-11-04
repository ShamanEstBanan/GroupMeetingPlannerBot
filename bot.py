import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config_data.config import Config, load_config
from handlers import base, meetings
from key_boards.main_menu import set_main_menu

from motor.motor_asyncio import AsyncIOMotorClient
logger = logging.getLogger(__name__)


async def main():

    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')
    logger.info('Starting bot')

    config: Config = load_config()

    # client = MongoClient("mongodb://localhost:27017/")  # Adjust the URI if needed

    fsm_storage: MongoStorage = MongoStorage(
        client = AsyncIOMotorClient(),
        db_name="bot_fsm",
        collection_name= "states_and_data"
    )

    bot: Bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp: Dispatcher = Dispatcher(storage=fsm_storage)

    await set_main_menu(bot)

    dp.include_router(base.router)
    dp.include_router(meetings.router)

    await bot.delete_webhook(drop_pending_updates=True) #убрать в продакшене
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error('Bot stopped!')


# async def main() -> None:
#     # Initialize Bot instance with default bot properties which will be passed to all API calls
#     bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
#
#     dp.include_router(meetings_router)
#
#     # And the run events dispatching
#     await dp.start_polling(bot)
#

# if __name__ == '__main__':
#     print('start to make bot')
#
#     logging.basicConfig(level=logging.INFO, stream=sys.stdout)
#     asyncio.run(main())
