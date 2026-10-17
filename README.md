# ATM PHANTOM — mise à jour préparée

## État

Fichiers préparés après inspection de bot.py, contenu.json, requirements.txt,
Dockerfile et railway.json du dépôt dydouubk/atm-phantom-bot,
révision 6325c6313bf2e7aaf7f37adb9a5ba913de238ed6.
Aucun push ni déploiement effectué.

La bannière d'origine fournie par l'utilisateur est incluse dans assets/banner.png,
sans retouche et sans modification de ses octets.
La bannière générée pendant la préparation a été exclue à la demande de l'utilisateur.

## Fichiers à remplacer dans le dépôt

- bot.py : photo avec légende, menu inline deux colonnes, édition du panneau,
  bouton @dxlx335, menu permanent de commandes, anciens boutons compatibles.
- contenu.json : accueil et rubriques rédigées pour des usages légitimes uniquement.
- Dockerfile : copie également le dossier assets dans l'image.
- Ajouter assets/banner.png : la véritable bannière d'origine (format PNG).
- test_bot.py : tests automatisés facultatifs dans le dépôt, non copiés dans l'image.

requirements.txt et railway.json sont fournis pour référence ; leurs paramètres
sont conservés (python-telegram-bot 22.8, une réplique Railway).
Ne jamais remplacer BOT_TOKEN : il reste exclusivement dans les variables Railway.
Ne pas ajouter de fichier .env au dépôt.

## Validation

Huit tests automatisés passent avec python-telegram-bot 22.8 : toutes les rubriques,
navigation des anciens menus, double clic, menu permanent, commandes répétées,
recréation d'un panneau supprimé, callback inconnu et propagation des erreurs inattendues.
Les appels Telegram sont simulés. Aucun test réel sur le bot en production,
aucune construction Docker et aucun déploiement Railway n'ont été effectués.
La bannière a été vérifiée : PNG lisible, dimensions et poids compatibles avec
l'envoi en photo. Les boutons dessinés dans l'image ne sont pas interactifs :
les véritables boutons Telegram apparaissent sous sa légende.

Après déploiement, ouvrir @ATMPhantom_Bot, envoyer /start,
vérifier la photo et les six rubriques, les retours, /menu et le contact @dxlx335.
Les clics inline modifient le même message. Le numéro du panneau reste en mémoire :
après redémarrage, la première commande crée un nouveau panneau ; les anciens
boutons continuent à fonctionner. Le menu permanent est le bouton de commandes
Telegram, pas un second clavier sous la zone de saisie.

Telegram ne permet pas de choisir arbitrairement le violet ou le chrome des boutons.
Son API propose des styles prédéfinis ; cette version garde le style natif.
Source : https://core.telegram.org/bots/api#inlinekeyboardbutton
Aucune statistique non mesurée ni faux badge de vérification n'est ajouté.

Le bot ne traite pas de remboursement, ne passe aucun appel, ne fabrique aucun
document et ne collecte pas de pièces personnelles. Les anciennes descriptions
évoquant l'usurpation bancaire et les pratiques trompeuses ont été remplacées.
