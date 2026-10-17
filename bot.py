"""ATM PHANTOM V3 — navigation Telegram, sans collecte de documents."""
import inspect
import json
import logging
import os
import sys
from html import escape
from pathlib import Path

from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonCommands
from telegram.constants import ParseMode
from telegram.error import BadRequest, Conflict, Forbidden, NetworkError, TelegramError
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

ROOT = Path(__file__).resolve().parent
BANNER = ROOT / "assets" / "banner.png"
CONTACT_URL = "https://t.me/dxlx335"
KEYS = ('Mutuelle🩺', 'Amazon📦', 'Call📞', 'Location🏠', 'Flyers🎨', 'Snap👻')
LABELS = dict(zip(KEYS, (
    "🩺 MUTUELLE", "📦 AMAZON", "📞 CALL", "🏠 LOCATION", "🎨 FLYERS", "👻 SNAP",
)))
STYLE_SUPPORTED = "style" in inspect.signature(InlineKeyboardButton).parameters
LOG = logging.getLogger(__name__)
CONTENT = None


def validate_text(value, label, maximum=None):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} : texte non vide attendu.")
    if maximum is not None and len(value) > maximum:
        raise ValueError(f"{label} : maximum {maximum} caractères.")
    return value


def raw_caption(data, key):
    if key == "menu":
        return data["accueil"]
    item = data["rubriques"][key]
    return item["titre"] + "\n\n" + item["texte"]


def load_content(path=None):
    path = ROOT / "contenu.json" if path is None else Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("contenu.json absent, illisible ou JSON invalide.") from None
    if not isinstance(data, dict) or not isinstance(data.get("rubriques"), dict):
        raise ValueError("contenu.json : objet accueil/rubriques attendu.")
    validate_text(data.get("accueil"), "accueil")
    for key in KEYS:
        item = data["rubriques"].get(key)
        if not isinstance(item, dict):
            raise ValueError("Rubrique absente ou invalide : " + key)
        validate_text(item.get("titre"), "Titre " + key, 40)
        validate_text(item.get("texte"), "Texte " + key)
    for key in ("menu", *KEYS):
        # Limite calculée sur le texte affiché, avant échappement HTML.
        if len(raw_caption(data, key).encode("utf-16-le")) // 2 > 1024:
            raise ValueError("Légende supérieure à 1024 unités UTF-16 : " + key)
    return data


def make_button(label, *, callback_data=None, url=None, style="primary"):
    options = {}
    if STYLE_SUPPORTED and os.environ.get("BUTTON_STYLES", "1") != "0":
        options["style"] = style
    return InlineKeyboardButton(label, callback_data=callback_data, url=url, **options)


def screen(key="menu"):
    if CONTENT is None:
        raise RuntimeError("Contenu non chargé.")
    if key == "menu":
        first, separator, rest = CONTENT["accueil"].partition("\n")
        caption = "<b>" + escape(first) + "</b>" + separator + escape(rest)
        buttons = [make_button(LABELS[k], callback_data=k) for k in KEYS]
        rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        rows.append([make_button("💬 CONTACTER @dxlx335", url=CONTACT_URL, style="success")])
    else:
        item = CONTENT["rubriques"][key]
        # Le JSON reste du texte brut : aucune balise fournie n'est exécutée.
        caption = "<b>" + escape(item["titre"]) + "</b>\n\n" + escape(item["texte"])
        rows = [[make_button("🏠 ACCUEIL", callback_data="menu"),
                 make_button("💬 CONTACT", url=CONTACT_URL, style="success")]]
    return caption, InlineKeyboardMarkup(rows)


def missing_panel(error):
    return any(reason in str(error).lower() for reason in (
        "message to edit not found", "message can't be edited",
        "message can not be edited", "there is no caption in the message to edit",
    ))


async def setup(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Bienvenue"),
        BotCommand("menu", "Ouvrir le menu ATM PHANTOM"),
    ])
    await app.bot.set_chat_menu_button(menu_button=MenuButtonCommands())


async def send_panel(update, context, key="menu"):
    if update.effective_chat is None:
        return
    caption, keyboard = screen(key)
    options = {}
    thread_id = getattr(update.effective_message, "message_thread_id", None)
    if thread_id is not None:
        options["message_thread_id"] = thread_id
    with BANNER.open("rb") as photo:
        message = await context.bot.send_photo(
            chat_id=update.effective_chat.id, photo=photo, caption=caption,
            parse_mode=ParseMode.HTML, reply_markup=keyboard, **options,
        )
    # Un panneau par sujet dans les groupes avec sujets.
    context.chat_data.setdefault("panels", {})[thread_id] = message.message_id


async def start(update, context):
    if update.effective_message is None or update.effective_chat is None:
        return
    thread_id = getattr(update.effective_message, "message_thread_id", None)
    panels = context.chat_data.setdefault("panels", {})
    message_id = panels.get(thread_id)
    if message_id is not None:
        caption, keyboard = screen()
        try:
            await context.bot.edit_message_caption(
                chat_id=update.effective_chat.id, message_id=message_id,
                caption=caption, parse_mode=ParseMode.HTML, reply_markup=keyboard,
            )
            return
        except BadRequest as error:
            if "message is not modified" in str(error).lower():
                return
            if not missing_panel(error):
                raise
            panels.pop(thread_id, None)
    await send_panel(update, context)


async def button(update, context):
    query = update.callback_query
    if query is None:
        return
    key = query.data
    valid = isinstance(key, str) and key in ("menu", *KEYS)
    try:
        await query.answer(None if valid else "Menu ancien : utilisez /menu.")
    except BadRequest as error:
        if any(s in str(error).lower() for s in ("query is too old", "query_id_invalid", "query id is invalid")):
            return
        raise
    if not valid:
        return
    message = query.message
    if message is None:
        return
    # Un ancien panneau texte est remplacé par une bannière.
    if not getattr(message, "photo", None):
        await send_panel(update, context, key)
        return
    caption, keyboard = screen(key)
    try:
        await query.edit_message_caption(
            caption=caption, parse_mode=ParseMode.HTML, reply_markup=keyboard,
        )
    except BadRequest as error:
        if "message is not modified" not in str(error).lower():
            if missing_panel(error):
                await send_panel(update, context, key)
                return
            raise
    if context.chat_data is not None:
        thread_id = getattr(message, "message_thread_id", None)
        context.chat_data.setdefault("panels", {})[thread_id] = message.message_id


async def on_error(update, context):
    # Ne jamais journaliser l'Update, l'URL des requêtes ou le jeton.
    error = context.error
    if isinstance(error, Conflict):
        LOG.error("Conflit Telegram : gardez une seule instance du bot en polling.")
    elif isinstance(error, Forbidden):
        LOG.warning("Accès au chat refusé ou bot bloqué.")
    elif isinstance(error, NetworkError):
        LOG.warning("Requête Telegram échouée (%s). Réessayez /menu.", type(error).__name__)
    else:
        LOG.error("Erreur de traitement (%s).", type(error).__name__)
    if isinstance(error, TelegramError) and not isinstance(error, (Forbidden, Conflict)):
        chat = getattr(update, "effective_chat", None)
        if chat is not None:
            try:
                await context.bot.send_message(chat.id, "Le menu n’a pas pu être actualisé. Réessayez /menu.")
            except TelegramError:
                pass


def main():
    global CONTENT
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    CONTENT = load_content()
    if not BANNER.is_file():
        raise SystemExit("Bannière manquante : assets/banner.png")
    if "--check" in sys.argv:
        for key in ("menu", *KEYS):
            screen(key)
        print("V3 : JSON, longueurs et claviers valides ; bannière présente.")
        print("Styles pris en charge par la bibliothèque :", STYLE_SUPPORTED)
        return
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN manquant dans les variables Railway.")
    app = Application.builder().token(token).post_init(setup).concurrent_updates(False).build()
    app.add_handler(CommandHandler(["start", "menu"], start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_error_handler(on_error)
    app.run_polling(allowed_updates=["message", "callback_query"], bootstrap_retries=3)


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        raise SystemExit(str(error)) from None
    except Exception as error:
        raise SystemExit(f"Démarrage interrompu ({type(error).__name__}). Vérifiez configuration et réseau.") from None
