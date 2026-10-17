# ATM PHANTOM — bot Telegram pour Railway

Bot destiné à **@ATMPhantom_Bot**, contact : https://t.me/dxlx335.
Le nom réel du bot est déterminé par le token fourni par BotFather : le code ne réserve ni ne change ce nom.

## Fonctionnalités

- `/start` et `/menu` ouvrent un menu inline de six rubriques.
- Remboursement Mutuelle
- Remboursement Amazon
- Allo/Call
- Dossier Location
- Flyers
- Filtres Snap
- Chaque rubrique propose un bouton contact et un retour au menu.

Ce bot affiche des textes fixes. Il ne génère pas de documents, ne passe pas d'appels,
ne traite pas de remboursements, n'encaisse pas de paiements et ne télécharge pas les fichiers reçus.
Il ne propose aucune fraude, usurpation bancaire ou falsification. Il ne stocke aucune conversation
dans une base de données ; les échanges restent soumis au fonctionnement de Telegram.

## Déploiement Railway

1. Décompressez le ZIP dans un dossier.
2. Placez les fichiers extraits à la racine d'un dépôt GitHub, de préférence privé.
   N'ajoutez aucun token ni fichier `.env` au dépôt.
3. Dans Railway, créez un projet et un service depuis ce dépôt GitHub.
4. Dans les **Variables** du service, ajoutez `BOT_TOKEN` avec le token de
   **@ATMPhantom_Bot** obtenu directement auprès de **@BotFather** dans Telegram.
   Ne partagez pas cette valeur dans un chat, une capture ou un fichier.
5. Déployez ou redéployez après l'ajout de cette variable. Le Dockerfile installe
   Python 3.12 et les dépendances ; `railway.json` configure `python bot.py`.
6. Gardez **une seule réplique**. Désactivez la mise en veille/serverless pour un
   service permanent. Aucun domaine public, port HTTP ou healthcheck HTTP n'est nécessaire :
   le bot utilise le long polling sortant vers Telegram.
7. Ouvrez https://t.me/ATMPhantom_Bot et envoyez `/start`. Essayez chaque rubrique,
   le retour au menu et le contact.

Railway reçoit les fichiers via le dépôt, pas simplement par l'ouverture du ZIP.
Alternative pour utilisateurs de la CLI Railway : depuis le dossier extrait, exécutez
`railway login`, `railway link`, puis `railway up` après avoir configuré le service et sa variable.

Le bot peut fonctionner quand votre ordinateur est éteint, tant que le service Railway
reste actif, financé selon votre offre et connecté à Telegram. Ce ZIP ne déploie pas le service à lui seul.

## Exécution locale facultative

Avec Python 3.12 :

```text
python -m venv .venv
python -m pip install -r requirements.txt
python bot.py
```

Activez l'environnement virtuel avant l'installation : sous Windows PowerShell,
`.\.venv\Scripts\Activate.ps1` ; sous macOS/Linux, `source .venv/bin/activate`.
Définissez au préalable `BOT_TOKEN` dans l'environnement de la session via votre méthode
habituelle de gestion des secrets. `.env.example` est un exemple vide et n'est pas chargé automatiquement.
Arrêtez l'instance Railway avant de lancer localement avec le même token.

## Dépannage

- `BOT_TOKEN manquant` : ajouter la variable puis redéployer.
- `InvalidToken` : vérifier que le secret vient du bon bot dans BotFather.
- `Conflict` : arrêter toute autre instance utilisant ce token et conserver une seule réplique.
  Une transition entre deux déploiements peut brièvement provoquer ce conflit.
- Pas de réponse : vérifier que le déploiement tourne, que le compte Railway dispose des
  ressources nécessaires et que Telegram est accessible. Tester `/start` en conversation privée.
- Token divulgué : le révoquer dans BotFather, remplacer la variable Railway et redéployer.

## Modifier le contenu soi-même

Tout le contenu affiché se trouve dans **contenu.json**. Aucun changement de Python n'est nécessaire.

1. Ouvrez `contenu.json` dans un éditeur de texte (par exemple VS Code).
2. Modifiez `accueil`, puis les champs `titre` et `texte` des rubriques.
3. Gardez les identifiants `mutuelle`, `amazon`, `call`, `location`, `flyers` et `snap` inchangés.
4. Enregistrez en UTF-8, envoyez la modification au dépôt et redéployez Railway.

Exemple de rubrique :

```json
"flyers": {
  "titre": "Flyers",
  "texte": "Votre présentation ici.\nUne deuxième ligne ici."
}
```

Utilisez `\n` pour un retour à la ligne et `\"` pour un guillemet dans un texte.
Conservez les virgules et les accolades du JSON. Les textes sont affichés tels quels,
sans HTML ni Markdown. Limitez chaque titre à 64 caractères et l'ensemble titre + texte
à 4096 unités UTF-16 (les emojis peuvent en occuper deux). Un contenu invalide empêche le démarrage.
Les rubriques sont livrées avec « Contenu à venir. » pour vous laisser les rédiger.
Il n'y a pas d'éditeur administrateur dans Telegram : les modifications passent par ce fichier.
Réservez le contenu aux démarches légitimes et aux documents authentiques.

Aucun token secret n'est fourni. Un test réel Telegram nécessite votre propre configuration.

## Documentation technique

- https://docs.python-telegram-bot.org/en/v22.8/
- https://docs.railway.com/config-as-code/reference
- https://docs.railway.com/deployments/start-command
- https://docs.railway.com/cli/deploying
