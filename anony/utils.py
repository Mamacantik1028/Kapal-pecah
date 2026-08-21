from telethon import __version__ as tv
from pyrogram import enums, types, __version__ as pv

from config import SUPPORT_CHAT

class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton
        self.style = enums.ButtonStyle

    def gen_key(self) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=f"Pyrogram v{pv}",
                        callback_data="pyrogram",
                        style=self.style.PRIMARY,
                    ),
                    self.ikb(
                        text=f"Telethon v{tv}",
                        callback_data="telethon",
                        style=self.style.PRIMARY,
                    ),
                ]
            ]
        )

    def pm_key(self, user_id: int) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text="Saved Messages",
                        url=f"tg://openmessage?user_id={user_id}",
                        style=self.style.SUCCESS,
                    )
                ]
            ]
        )

    def retry_key(self) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [[self.ikb(
                text="Try again",
                callback_data="generate",
                style=self.style.PRIMARY,
            )]]
        )

    def start_key(self) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [self.ikb(
                    text="Generate Session",
                    callback_data="generate",
                    style=self.style.PRIMARY,
                )],
                [
                    self.ikb(
                        text="Support",
                        url=SUPPORT_CHAT,
                        style=self.style.DANGER,
                    ),
                    self.ikb(
                        text="Source",
                        url="https://github.com/AnonymousX1025/StringGenBot",
                        style=self.style.DANGER,
                    ),
                ],
            ]
        )



import os
import ast
import traceback
from typing import Optional

async def meval(code: str, globs: dict, **kwargs):
    """
    Asynchronously evaluate a code string in a controlled environment.
    """

    # Copy globals to avoid mutation
    globs = globs.copy()

    # Special globals (for relative imports)
    _global_arg = "_globs"
    while _global_arg in globs:
        _global_arg = "_" + _global_arg

    kwargs[_global_arg] = {k: globs[k] for k in ("__name__", "__package__") if k in globs}

    root = ast.parse(code, mode="exec")
    if not root.body:
        return None

    ret_name = "_ret"
    while any(isinstance(n, ast.Name) and n.id == ret_name for n in ast.walk(root)) or ret_name in globs:
        ret_name = "_" + ret_name

    body = []
    body.append(ast.Expr(ast.Call(
        func=ast.Attribute(
            value=ast.Call(func=ast.Name(id="globals", ctx=ast.Load()), args=[], keywords=[]),
            attr="update", ctx=ast.Load()
        ),
        args=[], keywords=[ast.keyword(arg=None, value=ast.Name(id=_global_arg, ctx=ast.Load()))]
    )))
    body.append(ast.Assign(
        targets=[ast.Name(id=ret_name, ctx=ast.Store())],
        value=ast.List(elts=[], ctx=ast.Load())
    ))

    for node in root.body:
        if isinstance(node, ast.Expr):
            new_node = ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id=ret_name, ctx=ast.Load()), attr="append", ctx=ast.Load()),
                    args=[node.value], keywords=[]
                )
            )
            ast.copy_location(new_node, node)
            body.append(new_node)
        else:
            body.append(node)
    body.append(ast.Return(value=ast.Name(id=ret_name, ctx=ast.Load())))

    func_def = ast.AsyncFunctionDef(
        name="tmp",
        args=ast.arguments(
            posonlyargs=[], args=[], vararg=None,
            kwonlyargs=[ast.arg(arg=k) for k in kwargs.keys()],
            kw_defaults=[None] * len(kwargs),
            kwarg=None, defaults=[]
        ),
        body=body, decorator_list=[]
    )
    ast.fix_missing_locations(func_def)

    # Compile & execute
    locs = {}
    exec(compile(ast.Module([func_def], type_ignores=[]), "<meval>", "exec"), {}, locs)

    result = await locs["tmp"](**kwargs)
    if not result:
        return None
    result = [await r if hasattr(r, "__await__") else r for r in result]
    result = [r for r in result if r is not None]

    return result[0] if len(result) == 1 else (result or None)


def format_exception(exc: BaseException, tb: Optional[list[traceback.FrameSummary]] = None) -> str:
    """Format exception traceback into a readable string."""
    if tb is None:
        tb = traceback.extract_tb(exc.__traceback__)

    cwd = os.getcwd()
    for frame in tb:
        if cwd in frame.filename:
            frame.filename = os.path.relpath(frame.filename)

    return (
        "Traceback (most recent call last):\n"
        f"{''.join(traceback.format_list(tb))}"
        f"{type(exc).__name__}{': ' + str(exc) if str(exc) else ''}"
    )
