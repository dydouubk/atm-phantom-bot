"""ATM PHANTOM — menu informatif Telegram, sans collecte de documents."""
import json
import logging
from pathlib import Path
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

def load_content():
    path = Path(__file__).with_name("contenu.json")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    welcome = data["accueil"]
    if not isinstance(welcome, str) or not welcome.strip() or len(welcome.encode("utf-16-le")) // 2 > 4096:
        raise ValueError("Accueil vide ou trop long")
    sections = {}
    for key in ("mutuelle", "amazon", "call", "location", "flyers", "snap"):
        item = data["rubriques"][key]
        title, text = item["titre"], item["texte"]
        if not isinstance(title, str) or not title.strip() or len(title) > 64:
            raise ValueError("Titre invalide : " + key)
        if not isinstance(text, str) or len((title + "\n\n" + text).encode("utf-16-le")) // 2 > 4096:
            raise ValueError("Texte invalide ou trop long : " + key)
        sections[key] = (title, text)
    return welcome, sections


CONTACT_URL = "https://t.me/dxlx335"
WELCOME, SECTIONS = load_content()


def menu_keyboard():
    rows = [[InlineKeyboardButton(title, callback_data=key)]
            for key, (title, _) in SECTIONS.items()]
    rows.append([InlineKeyboardButton("Contact — @dxlx335", url=CONTACT_URL)])
    return InlineKeyboardMarkup(rows)


def section_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Contact — @dxlx335", url=CONTACT_URL)],
        [InlineKeyboardButton("← Retour au menu", callback_data="menu")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message:
        await update.effective_message.reply_text(WELCOME, reply_markup=menu_keyboard())


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    if query.data in SECTIONS:
        title, description = SECTIONS[query.data]
        text, keyboard = f"{title}\n\n{description}", section_keyboard()
    else:
        text, keyboard = WELCOME, menu_keyboard()
    try:
        await query.edit_message_text(text=text, reply_markup=keyboard)
    except BadRequest as error:
        # Un double clic peut demander exactement le même affichage.
        if "message is not modified" not in str(error).lower():
            raise


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    # Ne pas journaliser les messages, les URL API ou les exceptions avec leur token.
    logging.getLogger(__name__).error("Erreur de traitement : %s", type(context.error).__name__)


def main():
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN manquant : ajoutez-le dans les variables Railway.")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler(["start", "menu"], start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_error_handler(on_error)
    print("ATM PHANTOM : démarrage du bot.", flush=True)
    app.run_polling(allowed_updates=["message", "callback_query"], bootstrap_retries=3)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Une erreur au démarrage ne doit jamais afficher le token.
        raise SystemExit(f"Démarrage interrompu ({type(error).__name__}). Vérifiez la configuration et le réseau.") from None
