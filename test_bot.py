import unittest
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch, mock_open
from telegram.error import BadRequest
import bot


class BotTests(unittest.IsolatedAsyncioTestCase):
    def context(self):
        return NS(chat_data={}, bot=NS(edit_message_caption=AsyncMock()))

    def test_all_screens(self):
        for key in ('menu', *bot.KEYS):
            text, keyboard = bot.screen(key)
            self.assertLessEqual(len(text.encode('utf-16-le')) // 2, 1024)
            self.assertTrue(keyboard.inline_keyboard)
        rows = bot.screen()[1].inline_keyboard
        self.assertEqual([len(row) for row in rows], [2, 2, 2, 1])
        self.assertEqual(rows[-1][0].url, 'https://t.me/dxlx335')

    async def test_start_and_repeated_menu(self):
        ctx = self.context()
        msg = NS(reply_photo=AsyncMock(return_value=NS(message_id=42)))
        update = NS(effective_message=msg, effective_chat=NS(id=1))
        with patch('pathlib.Path.open', mock_open(read_data=b'original-banner')):
            await bot.start(update, ctx)
        self.assertEqual(ctx.chat_data['panel_id'], 42)
        await bot.start(update, ctx)
        msg.reply_photo.assert_awaited_once()
        ctx.bot.edit_message_caption.assert_awaited_once()

    async def test_deleted_panel_recreated(self):
        ctx = self.context()
        ctx.chat_data['panel_id'] = 2
        ctx.bot.edit_message_caption.side_effect = BadRequest('Message to edit not found')
        msg = NS(reply_photo=AsyncMock(return_value=NS(message_id=43)))
        with patch('pathlib.Path.open', mock_open(read_data=b'original-banner')):
            await bot.start(NS(effective_message=msg, effective_chat=NS(id=1)), ctx)
        self.assertEqual(ctx.chat_data['panel_id'], 43)

    async def test_navigation_and_legacy(self):
        for photo in (True, False):
            for key in (*bot.KEYS, *bot.LEGACY_KEYS, 'menu'):
                query = NS(data=key, message=NS(photo=photo, message_id=42),
                    answer=AsyncMock(), edit_message_caption=AsyncMock(), edit_message_text=AsyncMock())
                await bot.button(NS(callback_query=query), self.context())
                query.answer.assert_awaited_once()
                (query.edit_message_caption if photo else query.edit_message_text).assert_awaited_once()

    async def test_double_click(self):
        query = NS(data='menu', message=NS(photo=True, message_id=42), answer=AsyncMock(),
            edit_message_caption=AsyncMock(side_effect=BadRequest('Message is not modified')))
        await bot.button(NS(callback_query=query), self.context())

    async def test_unexpected_error_is_not_hidden(self):
        query = NS(data='menu', message=NS(photo=True, message_id=42), answer=AsyncMock(),
            edit_message_caption=AsyncMock(side_effect=BadRequest('Unexpected problem')))
        with self.assertRaises(BadRequest):
            await bot.button(NS(callback_query=query), self.context())

    async def test_unknown_callback(self):
        query = NS(data='old', answer=AsyncMock())
        await bot.button(NS(callback_query=query), self.context())
        query.answer.assert_awaited_once()

    async def test_permanent_menu(self):
        app = NS(bot=NS(set_my_commands=AsyncMock(), set_chat_menu_button=AsyncMock()))
        await bot.setup(app)
        app.bot.set_my_commands.assert_awaited_once()
        app.bot.set_chat_menu_button.assert_awaited_once()


if __name__ == '__main__':
    unittest.main()
