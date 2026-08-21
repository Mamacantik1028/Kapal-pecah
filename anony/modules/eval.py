import io
import os
import re
import sys
import uuid
import asyncio
import traceback

from html import escape
from pyrogram import filters, types
from typing import Any, Optional, Tuple

from anony import app
from anony.utils import meval, format_exception


@app.on_message(filters.command(["eval", "exec"]) & filters.user(app.OWNER))
@app.on_edited_message(filters.command(["eval", "exec"]) & filters.user(app.OWNER))
async def eval_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text("What?")

    code = message.text.split(None, 1)[1]
    out_buf = io.StringIO()

    async def _eval_code() -> Tuple[str, Optional[str]]:
        async def send(*args: Any, **kwargs: Any) -> types.Message:
            return await message.reply_text(*args, **kwargs)

        def _print(*args: Any, **kwargs: Any) -> None:
            kwargs.setdefault("file", out_buf)
            print(*args, **kwargs)

        eval_vars = {
            "m": message,
            "r": message.reply_to_message,
            "app": app,
            "client": app,
            "chat": message.chat,
            "user": message.from_user,
            "asyncio": asyncio,
            "sleep": asyncio.sleep,
            "ikb": types.InlineKeyboardButton,
            "ikm": types.InlineKeyboardMarkup,
            "pyrogram": sys.modules["pyrogram"],
            "send": send,
            "print": _print,
            "os": os,
            "re": re,
            "sys": sys,
            "tb": traceback,
            "traceback": traceback,
        }
        try:
            result = await meval(code, globals(), **eval_vars)
            return "", result
        except Exception as ex:
            tb = traceback.extract_tb(ex.__traceback__)
            snippet_tb = next(
                (i for i, f in enumerate(tb) if f.filename == "<string>"), -1
            )
            formatted_tb = format_exception(
                ex, tb[snippet_tb:] if snippet_tb != -1 else tb
            )
            return "⚠️ Error executing snippet\n\n", formatted_tb

    _, result = await _eval_code()

    if result is not None or not out_buf.getvalue():
        print(result, file=out_buf)

    output = out_buf.getvalue().strip()
    response = "<b>Output:</b>\n<code>{0}</code>".format(escape(output))

    if len(response) > 4096:
        with io.BytesIO(output.encode()) as out_file:
            out_file.name = f"{uuid.uuid4().hex[:8].lower()}.txt"
            return await message.reply_document(
                document=out_file, disable_notification=True
            )

    await message.reply_text(response)
