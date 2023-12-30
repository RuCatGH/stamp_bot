import asyncio
import os
import logging
import sys
import requests
from aiogram.types import BufferedInputFile
from aiogram import Bot
from playwright.async_api import async_playwright

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')

dp = Dispatcher()
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)


API_URL = "https://pkizh327c7.execute-api.us-west-2.amazonaws.com/prod/src20/latest?count=200"
CHECK_INTERVAL = 60*10  # seconds

async def check_token_growth(message: Message, page, tokens, last_block, json_response):
    range_blocks = range(last_block - 5, last_block + 1)
    have_growth = False
    for token in tokens:
        count = sum(1 for item in json_response if item['tick'] == token and int(item['block_index']) in range_blocks)
        
        if count >= 20:
            await message.answer(f"Рост {token}")
            have_growth = True
    if have_growth:
        await page.goto("https://www.stampscan.xyz/minting")
        await page.wait_for_timeout(5000)
        element = page.locator('canvas')

        # Наведение курсора на центр элемента
        element_handle = await element.hover()
        await page.wait_for_timeout(1000)

        # Take screenshot and send to chat
        screen = await page.screenshot(path='screenshot.png')
        await message.answer_photo(photo=BufferedInputFile(screen, ''))


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Бот запущен")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        while True:
            json_response = requests.get(API_URL).json()
            last_block = int(json_response[0]['block_index'])
            tokens = {item['tick'] for item in json_response}
            await check_token_growth(message, page, tokens, last_block, json_response)
            await asyncio.sleep(CHECK_INTERVAL)

async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())