"""ATM PHANTOM — navigation Telegram, sans collecte de documents."""
import json
import logging
import os
from pathlib import Path

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

ROOT = Path(__file__).resolve().parent
CONTACT_URL = "https://t.me/dxlx335"
KEYS = ("mutuelle", "amazon", "call", "location", "flyers", "snap")
LEGACY_KEYS = dict(zip(("Mutuelle🩺", "Amazon📦", "Call📞", "Location🏠", "Flyers🎨", "Snap👻"), KEYS))


def load_content():
    data = json.loads((ROOT / "contenu.json").read_text(encoding="utf-8-sig"))
    captions = [data["accueil"]]
    for key in KEYS:
        item = data["rubriques"][key]
        if not isinstance(item["titre"], str) or not 1 <= len(item["titre"]) <= 40:
            raise ValueError("Titre invalide : " + key)
        captions.append(item["titre"] + "\n\n" + item["texte"])
    for caption in captions:
        if not isinstance(caption, str) or not caption.strip() or len(caption.encode("utf-16-le")) // 2 > 1024:
            raise ValueError("Chaque légende doit contenir entre 1 et 1024 caractères UTF-16.")
    return data


CONTENT = load_content()


def screen(key="menu"):
    if key == "menu":
        buttons = [InlineKeyboardButton(CONTENT["rubriques"][k]["titre"], callback_data=k) for k in KEYS]
        rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        rows.append([InlineKeyboardButton("Contacter @dxlx335", url=CONTACT_URL)])
        return CONTENT["accueil"], InlineKeyboardMarkup(rows)
    item = CONTENT["rubriques"][key]
    return item["titre"] + "\n\n" + item["texte"], InlineKeyboardMarkup([[
        InlineKeyboardButton("← Accueil", callback_data="menu"),
        InlineKeyboardButton("Contact", url=CONTACT_URL),
    ]])


async def setup(app):
    await app.bot.set_my_commands([
        BotCommand("menu", "Ouvrir le menu ATM PHANTOM"),
        BotCommand("start", "Bienvenue"),
    ])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def start(update, context):
    if not update.effective_message or not update.effective_chat:
        return
    caption, keyboard = screen()
    # Les commandes répétées réutilisent le panneau tant qu'il existe.
    message_id = context.chat_data.get("panel_id")
    if message_id:
        try:
            await context.bot.edit_message_caption(chat_id=update.effective_chat.id,
                message_id=message_id, caption=caption, reply_markup=keyboard)
            return
        except BadRequest as error:
            reason = str(error).lower()
            if "message is not modified" in reason:
                return
            if not any(s in reason for s in ("message to edit not found", "message can't be edited")):
                raise
    with (ROOT / "assets" / "banner.png").open("rb") as photo:
        message = await update.effective_message.reply_photo(photo=photo, caption=caption, reply_markup=keyboard)
    context.chat_data["panel_id"] = message.message_id


async def button(update, context):
    query = update.callback_query
    if query is None:
        return
    key = LEGACY_KEYS.get(query.data, query.data)
    if key not in (*KEYS, "menu"):
        await query.answer("Menu ancien : utilisez /menu.")
        return
    await query.answer()
    caption, keyboard = screen(key)
    try:
        if query.message and query.message.photo:
            await query.edit_message_caption(caption=caption, reply_markup=keyboard)
            context.chat_data["panel_id"] = query.message.message_id
        else:
            # Compatibilité avec les anciens menus texte déjà envoyés.
            await query.edit_message_text(text=caption, reply_markup=keyboard)
    except BadRequest as error:
        reason = str(error).lower()
        if "message is not modified" in reason:
            return
        if any(s in reason for s in ("message to edit not found", "message can't be edited")):
            return  # /menu permet de recréer le panneau supprimé.
        raise


async def on_error(update, context):
    logging.getLogger(__name__).error("Erreur de traitement : %s", type(context.error).__name__)


def main():
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN manquant dans les variables Railway.")
    if not (ROOT / "assets" / "banner.png").is_file():
        raise SystemExit("Bannière manquante : assets/banner.png")
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    app = Application.builder().token(token).post_init(setup).concurrent_updates(False).build()
    app.add_handler(CommandHandler(["start", "menu"], start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_error_handler(on_error)
    app.run_polling(allowed_updates=["message", "callback_query"], bootstrap_retries=3)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit(f"Démarrage interrompu ({type(error).__name__}). Vérifiez configuration et réseau.") from None
