# Multi-LLM Debate CLI

> Un outil en ligne de commande, pensé pour les débutants, qui fait
> **débattre entre eux plusieurs modèles d'IA** au sujet de ton idée de
> projet avant que tu ne t'y engages — plutôt que d'interroger un seul
> modèle et d'espérer que sa réponse soit fiable.

## Table des matières

- [Pourquoi cet outil existe](#pourquoi-cet-outil-existe)
- [L'idée de base, en langage simple](#lidée-de-base-en-langage-simple)
- [Ce que "débat" veut vraiment dire ici](#ce-que-débat-veut-vraiment-dire-ici)
- [Pourquoi trois modèles plutôt qu'un ou deux](#pourquoi-trois-modèles-plutôt-quun-ou-deux)
- [Ce dont tu as besoin avant de commencer](#ce-dont-tu-as-besoin-avant-de-commencer)
- [Installation, étape par étape](#installation-étape-par-étape)
- [Obtenir tes clés API](#obtenir-tes-clés-api)
- [Ton premier essai (sans appel API, sans risque)](#ton-premier-essai-sans-appel-api-sans-risque)
- [Ton premier vrai débat](#ton-premier-vrai-débat)
- [Comprendre les cinq phases d'un débat](#comprendre-les-cinq-phases-dun-débat)
- [Lire les fichiers de sortie](#lire-les-fichiers-de-sortie)
- [Toutes les options en ligne de commande](#toutes-les-options-en-ligne-de-commande)
- [Construire un brief enrichi avec l'assistant interactif](#construire-un-brief-enrichi-avec-lassistant-interactif)
- [Bien choisir tes modèles](#bien-choisir-tes-modèles)
- [Ajouter un quatrième modèle ou fournisseur](#ajouter-un-quatrième-modèle-ou-fournisseur)
- [Coût et limites de débit](#coût-et-limites-de-débit)
- [Dépannage](#dépannage)
- [Questions fréquentes](#questions-fréquentes)
- [Projet lié : la version "chat" de ce workflow](#projet-lié--la-version-chat-de-ce-workflow)
- [Licence](#licence)

## Pourquoi cet outil existe

Si tu as déjà demandé à une seule IA « est-ce que c'est une bonne idée ? »,
tu connais déjà le problème : elle a tendance à être conciliante. Elle te
dit rarement « ce plan a un défaut fatal » à moins que tu ne l'y pousses
explicitement. Les différents modèles ont aussi des angles morts différents
: l'un sera excellent pour repérer les failles de sécurité et mauvais pour
questionner tes hypothèses de départ, un autre sera l'inverse.

Cet outil existe pour t'éviter de devoir deviner : il te donne
automatiquement un **deuxième, un troisième, voire un quatrième avis** sur
une idée de projet, un choix d'architecture ou une décision de design — de
façon structurée et reproductible, sans que tu aies à copier-coller du texte
d'un onglet de navigateur à l'autre à la main.

> **Remarque pour les grands débutants**
> Tu n'as pas besoin de savoir programmer pour utiliser cet outil. Tu dois
> juste être à l'aise pour taper quelques commandes dans un terminal, et
> avoir (ou être prêt à créer) des comptes gratuits ou payants chez les
> fournisseurs d'IA que tu veux utiliser. Chaque étape ci-dessous est
> expliquée comme si c'était la toute première fois.

## L'idée de base, en langage simple

Imagine que tu as une idée de projet. Plutôt que de demander l'avis d'un
seul ami, tu réunis trois amis qui ne connaissent pas encore l'avis des
autres, et tu demandes à chacun, séparément :

1. Qu'est-ce qui pourrait mal tourner avec cette idée ?
2. Qu'est-ce que je ne vois pas ?
3. Qu'est-ce que tu changerais ?

Ensuite, tu laisses chacun lire les réponses des autres et réagir — « je
suis d'accord sur ce point, pas sur celui-là, et voici pourquoi ». Enfin, tu
demandes à un quatrième ami, neutre, de lire toute la discussion et de te
donner un verdict final.

C'est exactement ce que cet outil automatise, sauf que tes trois (ou plus)
« amis » sont des modèles d'IA — par exemple GLM, DeepSeek et Qwen — et que
le quatrième « ami » qui donne le verdict final s'appelle le **juge**.

## Ce que "débat" veut vraiment dire ici

Une façon courante — et plus fragile — de combiner plusieurs IA est de les
**enchaîner** : tu interroges le modèle A, puis tu colles sa réponse dans le
modèle B en lui demandant de commenter, puis tu colles la réponse de B dans
le modèle C. Ça paraît logique, mais ça cache un défaut : toute erreur ou
angle mort introduit tôt par le modèle A a tendance à se **propager et à
s'amplifier** tout au long de la chaîne, parce que chaque modèle ne voit
jamais que le cadrage du modèle précédent, jamais le problème d'origine.

Cet outil évite ce piège grâce à un **protocole en cinq phases**, où chaque
modèle a toujours accès à ton brief d'origine, pas seulement à ce que le
modèle précédent en a dit. Le détail vient plus bas, mais en version
courte :

- **Phase 0** — chaque modèle cartographie silencieusement le problème seul
  (branches de décision, dépendances, ambiguïtés) avant de dire quoi que ce
  soit à voix haute.
- **Phase 1** — chaque modèle donne un premier avis, totalement indépendant.
- **Phase 2** — chaque modèle lit les premiers avis des *autres* modèles et
  réagit : ce qu'il garde, ce qu'il corrige, ce qu'il rejette.
- **Phase 3** — chaque modèle révise sa propre position une dernière fois.
- **Phase juge** — un modèle séparé lit tout et rend un verdict final,
  argumenté.

## Pourquoi trois modèles plutôt qu'un ou deux

- **Un seul modèle** te donne un avis, pas un vrai stress-test.
- **Deux modèles** te donnent un deuxième avis, ce qui est déjà utile, mais
  tu ne peux pas savoir si un désaccord signifie « l'un des deux se trompe »
  ou « c'est vraiment ambigu ».
- **Trois modèles** te permettent de commencer à voir des motifs : si deux
  sur trois signalent le même risque, ce risque est probablement réel. Si
  les trois sont en désaccord, tu as trouvé une vraie question ouverte, qui
  mérite d'être tranchée par toi-même.

Tu peux utiliser plus de trois modèles pour une couverture encore plus
large, mais garde en tête que le coût et le temps d'attente augmentent avec
chaque modèle supplémentaire, et qu'au-delà de trois ou quatre, le gain
d'information supplémentaire diminue généralement vite.

## Ce dont tu as besoin avant de commencer

- Un ordinateur avec **Python 3.10 ou plus récent** installé.
- Un terminal (sur Windows : PowerShell ; sur Android/Termux : le shell
  Termux ; sur macOS/Linux : ton terminal habituel).
- **Git**, pour télécharger (cloner) ce dépôt.
- Des comptes et des clés API chez les fournisseurs d'IA que tu veux
  utiliser — au moins deux, idéalement trois. Ce projet gère nativement :
  - **GLM** (via [Z.AI](https://www.z.ai))
  - **DeepSeek** (via la [plateforme DeepSeek](https://platform.deepseek.com))
  - **Qwen** (via [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com))

> **Remarque**
> Tu n'as pas besoin des trois. Deux est le minimum strict accepté par
> l'outil, mais trois est fortement recommandé, pour les raisons expliquées
> ci-dessus.

## Installation, étape par étape

1. **Clone le dépôt** (télécharge une copie sur ta machine) :

   ```bash
   git clone https://github.com/valorisa/multi-llm-debate-cli.git
   cd multi-llm-debate-cli
   ```

2. **Crée un environnement virtuel** (une installation Python isolée, rien
   que pour ce projet, qui n'interfère avec rien d'autre sur ta machine).
   Cette étape est optionnelle mais fortement recommandée :

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # sous Windows PowerShell : .venv\Scripts\Activate.ps1
   ```

3. **Installe les dépendances** (les bibliothèques externes dont cet outil a
   besoin pour parler à chaque fournisseur d'IA) :

   ```bash
   pip install -r requirements.txt
   ```

4. **Crée ton propre fichier `.env`** à partir du modèle fourni, puis
   renseigne les clés API que tu possèdes déjà (voir la section suivante si
   tu ne les as pas encore) :

   ```bash
   cp .env.example .env
   ```

   Ouvre ensuite `.env` dans n'importe quel éditeur de texte et colle tes
   clés après les signes `=`. Ce fichier est déjà exclu de Git (voir
   `.gitignore`), donc tes clés ne finiront jamais accidentellement sur
   GitHub.

## Obtenir tes clés API

Tu n'as besoin de clés que pour les fournisseurs que tu comptes réellement
utiliser.

- **Z.AI (pour GLM)** : crée un compte sur
  [z.ai](https://www.z.ai), puis génère une clé API depuis le tableau de
  bord de ton compte. Renseigne-la comme `ZAI_API_KEY` dans ton fichier
  `.env`.
- **DeepSeek** : crée un compte sur
  [platform.deepseek.com](https://platform.deepseek.com), puis génère une
  clé API. Renseigne-la comme `DEEPSEEK_API_KEY` dans ton fichier `.env`.
- **Qwen (DashScope)** : crée un compte sur
  [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com), puis
  génère une clé API. Renseigne-la comme `QWEN_API_KEY` dans ton fichier
  `.env`.

> **Remarque de sécurité**
> Traite ces clés comme des mots de passe. Ne les colle jamais directement
> dans un chat, une capture d'écran, ou une issue GitHub publique. Si tu
> soupçonnes qu'une clé a fuité, révoque-la immédiatement depuis le tableau
> de bord du fournisseur et génères-en une nouvelle.

## Ton premier essai (sans appel API, sans risque)

Avant de dépenser le moindre crédit API, lance l'outil en **mode dry-run**.
Ce mode simule l'intégralité du protocole en cinq phases avec des réponses
factices, pour que tu puisses confirmer que tout est correctement installé
et comprendre à quoi ressemble la sortie :

```bash
python debate_cli.py \
  --brief "Je veux créer un petit outil en ligne de commande qui convertit des fichiers CSV en JSON." \
  --models glm,deepseek,qwen \
  --judge glm \
  --dry-run
```

Si l'exécution se termine par un message du type
`Résultats enregistrés dans debate_output/`, ton installation fonctionne
correctement.

## Ton premier vrai débat

Une fois que ton fichier `.env` contient de vraies clés API, retire
`--dry-run` et relance la même commande — cette fois, elle fera de vrais
appels vers chaque fournisseur :

```bash
python debate_cli.py \
  --brief "Je veux créer un petit outil en ligne de commande qui convertit des fichiers CSV en JSON." \
  --models glm,deepseek,qwen \
  --judge glm
```

> **Astuce pour un meilleur débat**
> Plus tu mets de détails dans `--brief`, meilleur sera le débat. Une idée
> en une ligne fonctionne, mais un court paragraphe couvrant l'objectif, les
> utilisateurs cibles, les contraintes, et ce que tu veux spécifiquement
> voir challengé produira un débat bien plus utile. Tu peux aussi mettre un
> brief plus long dans un fichier texte et le passer avec
> `--brief-file mon-brief.txt` au lieu de `--brief`.

## Comprendre les cinq phases d'un débat

| Phase | Nom | Ce qui se passe | Qui voit quoi |
|---|---|---|---|
| 0 | Cadrage silencieux | Chaque modèle cartographie en privé les branches de décision, les dépendances et les ambiguïtés de ton brief. | Chaque modèle ne voit que ton brief. |
| 1 | Position initiale | Chaque modèle donne sa première analyse complète et indépendante : points forts, points faibles, risques critiques. | Chaque modèle ne voit que ton brief (pas encore les réponses des autres). |
| 2 | Lecture croisée | Chaque modèle lit les réponses de Phase 1 des *autres* modèles et réagit : ce qu'il garde, corrige ou rejette. | Chaque modèle voit ton brief + les réponses de Phase 1 des autres. |
| 3 | Révision finale | Chaque modèle produit une position consolidée et mise à jour après la lecture croisée. | Chaque modèle voit ses propres réponses de Phase 1 et Phase 2. |
| Juge | Arbitrage | Un modèle séparé (ou le même) lit toute la trajectoire de chaque modèle et rend un verdict final argumenté. | Le juge voit tout, de tous les modèles. |

Après la phase du juge, l'outil demande automatiquement à un modèle de
transformer le verdict du juge en un court document de **synthèse** —
celui que tu voudras lire en premier.

## Lire les fichiers de sortie

Chaque exécution crée un dossier (`debate_output/` par défaut, modifiable
avec `--output-dir`) contenant :

- `brief.txt` — le brief exact utilisé pour cette exécution, pour toujours
  savoir ce qui a été débattu.
- `rounds.json` — la réponse de chaque modèle à chaque phase, dans l'ordre
  (`[Phase 0, Phase 1, Phase 2, Phase 3]`), utile si tu veux relire tout le
  cheminement du raisonnement.
- `judge.txt` — l'arbitrage complet du modèle juge.
- `synthesis.txt` — le résumé final, court et lisible. **Commence par
  celui-là.**
- `meta.json` — les métadonnées techniques de l'exécution (horodatage,
  modèles utilisés, modèle juge, modèle de synthèse).

## Toutes les options en ligne de commande

| Option | Obligatoire | Valeur par défaut | Signification |
|---|---|---|---|
| `--brief` | l'un de `--brief` / `--brief-file` | — | Ton idée de projet, écrite directement en ligne de commande. |
| `--brief-file` | l'un de `--brief` / `--brief-file` | — | Chemin vers un fichier texte contenant ton idée de projet. |
| `--models` | non | `glm,deepseek,qwen` | Liste de modèles séparés par des virgules avec qui débattre. |
| `--judge` | non | `glm` | Quel modèle arbitre à la fin. |
| `--synthesis-model` | non | identique à `--judge` | Quel modèle rédige le résumé final. |
| `--max-retries` | non | `2` | Combien de fois redemander à un modèle de corriger sa réponse si elle ne suit pas la structure attendue. |
| `--output-dir` | non | `debate_output` | Où enregistrer les fichiers de résultat. |
| `--dry-run` | non | désactivé | Simule l'ensemble de l'exécution avec des réponses factices, sans appeler de vraie API. |

## Construire un brief enrichi avec l'assistant interactif

Un bon débat repose sur un bon brief. Le script `build_brief.py` vous guide à travers une série de questions pour construire un `brief.txt` détaillé – sans avoir à le rédiger de zéro.

**Utilisation de base** (assistant interactif) :

```bash
python build_brief.py
```

Vous serez interrogé sur :
- la nature du projet,
- son objectif principal,
- les utilisateurs cibles,
- les contraintes,
- les choix déjà faits,
- ce que vous voulez spécifiquement challenger,
- les risques connus,
- les critères de succès.

Les réponses peuvent être multilignes (ligne vide pour terminer). Le script produit deux fichiers :
- `brief.txt` – prêt à être passé à `debate_cli.py --brief-file`
- `brief.json` – les réponses brutes, permettant de recharger et modifier ultérieurement.

**Réutiliser un brief précédent** (sans tout retaper) :

```bash
python build_brief.py --from-json brief.json --output mon-nouveau-brief.txt
```

**Enrichir avec un LLM** (optionnel, nécessite des clés API et une copie de `debate_cli.py`) :

```bash
python build_brief.py --enrich --enrich-model glm
```

Cette option envoie votre brief à un modèle de langage qui le reformule et l’étoffe en un texte plus dense et plus clair – sans inventer de faits. Si la version enrichie manque une section obligatoire, le script conserve le brief original.

**Enchaîner directement vers un débat** (une seule commande, de bout en bout) :

```bash
python build_brief.py --then-debate --models glm,deepseek,qwen --judge glm
```

Après avoir terminé l'assistant, le script lance automatiquement `debate_cli.py` avec le brief généré. Si le débat échoue, un message d'erreur explicite s'affiche.

**Toutes les options de `build_brief.py`** :

| Option | Défaut | Signification |
|--------|--------|---------------|
| `--output` | `brief.txt` | Fichier de sortie pour le brief final. |
| `--save-json` | `<output>.json` | Où sauvegarder les réponses brutes en JSON. |
| `--from-json` | – | Recharger les réponses d'un fichier JSON précédent (ignore l'assistant). |
| `--enrich` | désactivé | Enrichir le brief via un LLM. |
| `--enrich-model` | `glm` | Modèle pour l'enrichissement (glm, deepseek, qwen). |
| `--debate-cli-path` | `debate_cli.py` | Chemin vers `debate_cli.py` (pour l'enrichissement et l'enchaînement). |
| `--then-debate` | désactivé | Lancer automatiquement `debate_cli.py` après la construction du brief. |
| `--models` | `glm,deepseek,qwen` | Modèles à utiliser si `--then-debate` est activé. |
| `--judge` | `glm` | Modèle juge pour `--then-debate`. |
| `--dry-run` | désactivé | Passer `--dry-run` à `debate_cli.py` lors de l'enchaînement. |

> **Conseil** : gardez `build_brief.py` dans le même dossier que `debate_cli.py` – il importe la logique de routage pour l'enrichissement et l'enchaînement. Si vous les déplacez, utilisez `--debate-cli-path`.

## Bien choisir tes modèles

Une bonne règle générale, inspirée des vraies pratiques de revue
multi-agents : donne à chaque modèle un **rôle** distinct plutôt que de
poser aux trois exactement la même question générique. Par exemple :

- Un modèle concentré sur l'**architecture et la structure** — le plan
  est-il bien organisé, les éléments sont-ils dans le bon ordre ?
- Un modèle concentré sur la **faisabilité d'implémentation** — est-ce
  réellement réalisable avec la stack proposée, dans le délai proposé ?
- Un modèle concentré sur la **revue critique** — préoccupations de
  sécurité, cas limites oubliés, hypothèses jamais vérifiées.

Tu orientes cela par la façon dont tu formules ton `--brief` : demande
explicitement, à la fin de ton brief, que chacun de ces angles soit couvert,
et les modèles s'y prêteront naturellement pendant le débat.

Pour le **juge**, privilégie si possible un modèle qui n'était **pas** l'un
des trois débatteurs — un modèle qui n'a rien à défendre de sa propre
réponse précédente a tendance à arbitrer plus équitablement. Si tu n'as
accès qu'à un seul modèle vraiment solide, le réutiliser comme juge reste
largement préférable à sauter complètement la phase de jugement.

## Ajouter un quatrième modèle ou fournisseur

Le routage entre le nom court d'un modèle (`"glm"`, `"deepseek"`, `"qwen"`)
et le véritable appel API se trouve à un seul endroit : la fonction
`make_call_llm()`, près du début de `debate_cli.py`. Pour ajouter un nouveau
fournisseur :

1. Écris une fonction `call_<fournisseur>(prompt: str) -> str`, en suivant
   le modèle des fonctions existantes `call_glm`, `call_deepseek` et
   `call_qwen`.
2. Ajoute ta fonction de récupération de clé API
   (`get_<fournisseur>_api_key()`), en lisant l'environnement de la même
   façon que les fonctions existantes.
3. Enregistre ta fonction dans le dictionnaire `dispatch`, à l'intérieur de
   `make_call_llm()`.
4. Passe le nom court de ton fournisseur à `--models` et, si tu le souhaites,
   à `--judge`.

## Coût et limites de débit

Un débat complet avec 3 modèles effectue environ :

- 3 appels pour la Phase 0
- 3 appels pour la Phase 1
- 3 appels pour la Phase 2
- 3 appels pour la Phase 3
- 1 appel pour le juge
- 1 appel pour la synthèse

Soit **14 appels API au minimum** par débat, davantage si la réponse d'un
modèle nécessite une relance pour respecter le format attendu. Pour une idée
simple, cela peut être disproportionné — lance toujours `--dry-run` en
premier, et réserve les vrais débats aux décisions qui justifient réellement
le coût et le temps d'attente.

## Dépannage

- **`ZAI_API_KEY manquante dans l'environnement`** — ton fichier `.env`
  n'existe pas encore, n'a pas été rempli, ou n'a pas été chargé.
  Assure-toi d'avoir bien copié `.env.example` vers `.env` et que la clé y
  est réellement collée.
- **`Le modèle X n'a pas respecté le format... après N tentatives`** — cela
  signifie qu'un modèle a continué à répondre en texte libre au lieu du
  format structuré attendu par l'outil, même après qu'on lui a demandé de se
  corriger. Essaie d'augmenter `--max-retries`, ou confie ce rôle à un autre
  modèle, plus rigoureux dans le suivi des instructions.
- **`Modèle 'x' non supporté`** — tu as passé un nom de modèle dans
  `--models` ou `--judge` qui n'est pas enregistré dans `make_call_llm()`.
  Vérifie l'orthographe (`glm`, `deepseek`, `qwen`), ou ajoute le support
  pour ce modèle (voir la section ci-dessus sur l'ajout d'un nouveau
  fournisseur).
- **Rien ne se passe pendant longtemps** — c'est normal, surtout avec 3
  modèles et 4 phases ; un débat complet peut prendre plusieurs minutes
  selon le temps de réponse de chaque fournisseur.

## Questions fréquentes

**Dois-je comprendre le protocole de débat pour utiliser cet outil ?**
Non. L'outil gère l'intégralité du protocole pour toi. Lire la section
« Comprendre les cinq phases » ci-dessus t'aidera à mieux interpréter la
sortie, mais ce n'est pas nécessaire pour lancer un débat.

**Puis-je l'utiliser avec seulement deux modèles ?**
Oui, deux est le minimum technique. Trois est recommandé car cela permet une
forme basique de consensus (« 2 sur 3 s'accordent sur ce risque »).

**Puis-je l'utiliser sans aucune expérience de programmation ?**
Oui. Tu n'as besoin d'écrire ou de modifier aucun code Python pour utiliser
cet outil au quotidien — seulement pour ajouter un nouveau fournisseur d'IA,
ce qui est optionnel.

**Est-ce la même chose que de discuter avec trois onglets de navigateur
ouverts ?**
Ça automatise et structure ce que tu devrais sinon faire manuellement en
copiant-collant entre onglets de navigateur — avec l'avantage supplémentaire
que le format de chaque réponse est vérifié automatiquement et, si besoin,
le modèle est invité à se corriger lui-même.

## Projet lié : la version "chat" de ce workflow

Si tu ne veux pas configurer de clés API et préfères utiliser à la main les
interfaces de chat web gratuites de GLM, DeepSeek, Claude, Qwen et
équivalents, le même protocole de débat est aussi disponible sous forme de
**fichier skill** portable, à coller directement dans n'importe quel chat :
voir la skill
[`multi-llm-debate-grill-me`](https://github.com/valorisa/Claude-Skills/tree/main/skills/multi-llm-debate-grill-me)
dans le dépôt [Claude-Skills](https://github.com/valorisa/Claude-Skills).
Cet outil en ligne de commande suit exactement le même protocole, simplement
automatisé de bout en bout plutôt que copié-collé à la main.

## Licence

Ce projet est publié sous [licence MIT](./LICENSE) — tu es libre de
l'utiliser, de le modifier et de le redistribuer, y compris à des fins
commerciales, tant que tu conserves la mention de copyright.

## Un dernier mot sur ce qu'est (et n'est pas) cet outil

Cet outil t'aide à **stress-tester la cohérence interne** d'un plan ou d'un
design en l'exposant à plusieurs lectures critiques et indépendantes. Il ne
remplace pas de vrais tests, un vrai audit de sécurité, ou de vrais retours
utilisateurs. Un plan peut parfaitement survivre à un débat et échouer quand
même dans la réalité — mais un plan qui survit à un véritable débat
multi-modèles est, en moyenne, un bien meilleur point de départ qu'un plan
qui n'a jamais été challengé du tout.
