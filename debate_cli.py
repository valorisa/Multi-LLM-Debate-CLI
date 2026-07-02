#!/usr/bin/env python3
"""
DebateOrchestrator CLI — Multi-LLM « multi-llm-debate-grill-me »

Orchestre un débat structuré entre plusieurs LLM (Round 0, 1, 2, 3, juge final),
avec vérification de format, relance, et synthèse structurée.

Clés API attendues dans l'environnement (ou un fichier .env chargé au préalable) :
    ZAI_API_KEY, DEEPSEEK_API_KEY, QWEN_API_KEY (DashScope)

Usage :
    python debate_cli.py --brief "Je veux créer un repo GitHub..."
    python debate_cli.py --brief-file brief.txt
    python debate_cli.py --models glm,deepseek,qwen --judge glm
"""

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# =========================
# Templates de prompts
# =========================

SKILL_TEXT = """
---
name: multi-llm-debate-grill-me
description: Organise un débat structuré entre plusieurs LLM sur un plan, un design ou une idée de projet, avec un cadrage silencieux de type "grill me", des rounds de critique croisée, puis un juge final.
---

# Multi-LLM Debate + Grill Me

> Objectif : tester un plan, un design ou une idée de projet par débat multi-agent, en commençant par un cadrage silencieux de type "grill me", puis en faisant converger les modèles vers une synthèse utile et critique.

## Principes

1. Chaque LLM reçoit le même brief initial.
2. Chaque LLM travaille d'abord de manière indépendante.
3. Les réponses des autres LLM ne sont introduites qu'après la première position.
4. Chaque round suit un format stable.
5. Le débat privilégie la clarté, la critique utile et la détection des angles morts.
6. Ne pas inventer de faits absents du brief.
7. Ne pas faire de recommandations globales avant la phase de synthèse.
8. Le juge final arbitre les divergences et produit une décision consolidée.

## Round 0 — Cadrage silencieux

### But
Activer mentalement la logique "grill me" avant tout débat visible.

### Instructions
- Lire le brief.
- Exécuter mentalement la skill "grill me".
- Identifier les branches de décision.
- Identifier les dépendances entre branches.
- Identifier les ambiguïtés, hypothèses implicites et zones à risque.
- Préparer une position initiale.
- Ne pas produire encore de critique complète.

### Sortie attendue

## Round 0 — Cadrage silencieux

### Branches de décision
- ...

### Dépendances
- ...

### Ambiguïtés
- ...

### Questions prioritaires
- ...

### Préparation pour Round 1
- ...

## Round 1 — Position initiale

### But
Donner une analyse autonome sans tenir compte des autres réponses.

### Instructions
- Produire une analyse initiale indépendante.
- Ne pas tenir compte des autres réponses.
- Être critique mais utile.
- Distinguer faits, hypothèses, risques et recommandations.
- Prioriser les blocages avant les améliorations mineures.

### Sortie attendue

## Round 1 — Position initiale

### Résumé du problème
- ...

### Hypothèses implicites
- ...

### Points forts
- ...

### Points faibles
- ...

### Risques critiques
- ...

### Questions de clarification
- ...

### Recommandations provisoires
- ...

### Verdict provisoire
- ...

## Round 2 — Lecture croisée

### But
Réagir aux réponses des autres LLM.

### Instructions
- Lire les positions des autres LLM.
- Dire ce qui est conservé, corrigé, rejeté.
- Expliquer les divergences importantes.
- Réviser l'analyse si nécessaire.
- Garder visibles les risques encore ouverts.
- Ne pas se contenter de dire "je suis d'accord".

### Sortie attendue

## Round 2 — Lecture croisée

### Ce que je conserve
- ...

### Ce que je corrige
- ...

### Ce que je rejette
- ...

### Divergences importantes
- ...

### Révision de mon analyse
- ...

### Risques toujours ouverts
- ...

## Round 3 — Révision finale

### But
Produire une version consolidée après débat.

### Instructions
- Intégrer les critiques pertinentes.
- Réduire les points faibles.
- Mettre à jour le niveau de confiance.
- Garder les incertitudes restantes visibles.
- Produire des recommandations finales exploitables.

### Sortie attendue

## Round 3 — Révision finale

### Position consolidée
- ...

### Ce qui a changé
- ...

### Risques restants
- ...

### Points encore incertains
- ...

### Recommandations finales
- ...

### Verdict final provisoire
- ...

## Juge final

### But
Synthétiser le débat et arbitrer.

### Instructions
- Comparer les arguments.
- Repérer les convergences.
- Signaler les divergences structurantes.
- Identifier les points les plus solides.
- Trancher si possible.
- Signaler ce qui reste incertain.
- Ne pas compter uniquement les votes.

### Sortie attendue

## Juge final

### Synthèse des convergences
- ...

### Synthèse des divergences
- ...

### Arguments les plus solides
- ...

### Points de vigilance majeurs
- ...

### Décision finale
- ...

### Niveau de confiance
- ...

### Ce qu'il faut faire ensuite
- ...

## Avertissement

Ce protocole teste la cohérence interne d'un plan ou d'un design, pas sa validité externe ni sa faisabilité réelle.
"""


def get_prompt_round_0(brief: str) -> str:
    return f"""
{SKILL_TEXT}

Tu dois commencer par le Round 0 (cadrage silencieux).

Brief :
{brief}

Consignes :
- Identifie les branches de décision, les dépendances, les ambiguïtés, les questions de clarification.
- Ne donne pas encore de synthèse finale.
- Réponds dans le format demandé par la skill.
"""


def get_prompt_round_1(brief: str) -> str:
    return f"""
{SKILL_TEXT}

Tu dois maintenant faire le Round 1 (position initiale).

Brief :
{brief}

Consignes :
- Sois critique, utile et structuré.
- Ne tiens pas compte des autres réponses.
- Réponds avec le format demandé par la skill.
"""


def get_prompt_round_2(brief: str, other_responses: List[str]) -> str:
    others_text = "\n\n".join(other_responses)
    return f"""
{SKILL_TEXT}

Tu dois maintenant faire le Round 2 (lecture croisée).

Brief :
{brief}

Voici les réponses des deux autres modèles :

{others_text}

Consignes :
- Révise ta position en conséquence.
- Réponds avec :
  - ce que tu conserves ;
  - ce que tu corriges ;
  - ce que tu rejettes ;
  - les divergences importantes ;
  - la révision de ton analyse ;
  - les risques toujours ouverts.
- Tu dois expliciter au moins un point que tu corriges et un point que tu rejettes.
- Tu ne peux pas dire seulement « je suis d'accord ».
"""


def get_prompt_round_3(brief: str, previous_response: str, round_2_response: str) -> str:
    return f"""
{SKILL_TEXT}

Tu dois maintenant faire le Round 3 (révision finale).

Brief :
{brief}

Ta réponse initiale (Round 1) :
{previous_response}

Ta réponse après lecture croisée (Round 2) :
{round_2_response}

Consignes :
- Intègre les critiques pertinentes.
- Réduis les points faibles.
- Mets à jour l'état de confiance.
- Garde les incertitudes visibles.
- Tu dois expliciter au moins un point qui a changé entre Round 2 et Round 3.
"""


def get_prompt_judge(brief: str, all_responses: Dict[str, List[str]]) -> str:
    summary = ""
    for model, rounds in all_responses.items():
        summary += f"\n\n### Modèle {model}\n"
        summary += f"Round 0:\n{rounds[0]}\n\n"
        summary += f"Round 1:\n{rounds[1]}\n\n"
        summary += f"Round 2:\n{rounds[2]}\n\n"
        summary += f"Round 3:\n{rounds[3]}\n\n"

    return f"""
{SKILL_TEXT}

Tu es le juge final.

Brief :
{brief}

Voici toutes les réponses des modèles :

{summary}

Consignes :
- Compare les arguments, pas seulement les conclusions.
- Repère les convergences.
- Signale les divergences structurantes.
- Identifie les arguments les plus solides.
- Donne une décision finale.
- Précise le niveau de confiance.
- Si un point reste incertain, tu dois le signaler explicitement.
- Tu ne dois pas simplement compter les votes. Tu dois évaluer la force des arguments.
"""


def get_prompt_brief_format(raw_text: str) -> str:
    return f"""
Tu dois transformer ce texte en un brief structuré pour un projet GitHub.

Voici le texte :

{raw_text}

Structure :

# Brief du projet

## 1.1. Sujet
- ...

## 1.2. Objectif
- ...

## 1.3. Utilisateurs cibles
- ...

## 1.4. Contraintes
- ...

## 1.5. Choix déjà faits
- ...

## 1.6. Ce que tu veux challenger
- ...

Sois clair et précis.
"""


def get_prompt_synthesis(brief: str, judge_response: str) -> str:
    return f"""
Tu dois produire un document de synthèse structuré à partir du juge final.

Brief :
{brief}

Juge final :
{judge_response}

Structure :

# Synthèse du débat Multi-LLM

## Convergences
- ...

## Divergences
- ...

## Risques majeurs
- ...

## Options proposées
- ...

## Recommandations
- ...

## Incertitudes
- ...

## Décision proposée
- ...

Sois clair et concis.
"""


# =========================
# Gestion d'erreurs
# =========================

class DebateError(Exception):
    pass


class LLMCallError(DebateError):
    pass


class FormatError(DebateError):
    pass


# =========================
# Vérification de format
# =========================
#
# NOTE (correction) : la vérification originale comparait les titres tels
# quels ("## Round 0 — Cadrage silencieux", avec tiret cadratin et apostrophe
# typographique). En pratique un LLM peut répondre avec un tiret simple ou une
# apostrophe droite sans que le fond soit incorrect. On normalise donc le
# texte avant comparaison (accents conservés, ponctuation typographique et
# espaces normalisés) pour éviter des relances inutiles qui gaspillent des
# tokens et peuvent épuiser max_retries pour un simple désaccord de glyphe.

def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("—", "-").replace("–", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


REQUIRED_ROUND_0 = [
    "## Round 0 - Cadrage silencieux",
    "### Branches de décision",
    "### Dépendances",
    "### Ambiguïtés",
    "### Questions prioritaires",
    "### Préparation pour Round 1",
]

REQUIRED_ROUND_1 = [
    "## Round 1 - Position initiale",
    "### Résumé du problème",
    "### Hypothèses implicites",
    "### Points forts",
    "### Points faibles",
    "### Risques critiques",
    "### Questions de clarification",
    "### Recommandations provisoires",
    "### Verdict provisoire",
]

REQUIRED_ROUND_2 = [
    "## Round 2 - Lecture croisée",
    "### Ce que je conserve",
    "### Ce que je corrige",
    "### Ce que je rejette",
    "### Divergences importantes",
    "### Révision de mon analyse",
    "### Risques toujours ouverts",
]

REQUIRED_ROUND_3 = [
    "## Round 3 - Révision finale",
    "### Position consolidée",
    "### Ce qui a changé",
    "### Risques restants",
    "### Points encore incertains",
    "### Recommandations finales",
    "### Verdict final provisoire",
]

REQUIRED_JUDGE = [
    "## Juge final",
    "### Synthèse des convergences",
    "### Synthèse des divergences",
    "### Arguments les plus solides",
    "### Points de vigilance majeurs",
    "### Décision finale",
    "### Niveau de confiance",
    "### Ce qu'il faut faire ensuite",
]


def check_sections(response: str, required: List[str]) -> bool:
    normalized_response = _normalize(response)
    return all(_normalize(s) in normalized_response for s in required)


def check_format_round_0(response: str) -> bool:
    return check_sections(response, REQUIRED_ROUND_0)


def check_format_round_1(response: str) -> bool:
    return check_sections(response, REQUIRED_ROUND_1)


def check_format_round_2(response: str) -> bool:
    return check_sections(response, REQUIRED_ROUND_2)


def check_format_round_3(response: str) -> bool:
    return check_sections(response, REQUIRED_ROUND_3)


def check_format_judge(response: str) -> bool:
    return check_sections(response, REQUIRED_JUDGE)


# =========================
# Appels API réels (GLM / DeepSeek / Qwen)
# =========================
#
# NOTE (correction) : dans la discussion Perplexity d'origine, ces fonctions
# étaient éparpillées sur plusieurs blocs successifs, avec des versions à clé
# API en dur (à éviter absolument, cf. "YOUR_API_KEY" en clair) puis une
# version via variables d'environnement. On ne garde que la version env vars.
# Les imports sont volontairement faits à l'intérieur des fonctions pour que
# le script tourne même si un seul des trois SDK est installé.

def get_zai_api_key() -> Optional[str]:
    return os.getenv("ZAI_API_KEY")


def get_deepseek_api_key() -> Optional[str]:
    return os.getenv("DEEPSEEK_API_KEY")


def get_qwen_api_key() -> Optional[str]:
    return os.getenv("QWEN_API_KEY")


def call_glm(prompt: str, model_name: str = "glm-5.2", timeout_sec: float = 60.0) -> str:
    from zai import ZaiClient  # pip install zai

    api_key = get_zai_api_key()
    if not api_key:
        raise LLMCallError("ZAI_API_KEY manquante dans l'environnement.")
    client = ZaiClient(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout_sec,
    )
    return response.choices[0].message.content


def call_deepseek(prompt: str, model_name: str = "deepseek-chat", timeout_sec: float = 60.0) -> str:
    from openai import OpenAI  # pip install openai

    api_key = get_deepseek_api_key()
    if not api_key:
        raise LLMCallError("DEEPSEEK_API_KEY manquante dans l'environnement.")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        timeout=timeout_sec,
    )
    return response.choices[0].message.content


def call_qwen(prompt: str, model_name: str = "qwen-max", timeout_sec: float = 60.0) -> str:
    import dashscope  # pip install dashscope
    from dashscope import Generation

    api_key = get_qwen_api_key()
    if not api_key:
        raise LLMCallError("QWEN_API_KEY manquante dans l'environnement.")
    dashscope.api_key = api_key
    response = Generation.call(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        result_format="message",
        timeout=timeout_sec,
    )
    if response.status_code != 200:
        raise LLMCallError(f"Erreur Qwen ({response.status_code}) : {response.message}")
    return response.output.choices[0].message.content


def make_call_llm() -> Callable[[str, str], str]:
    """
    Construit la fonction call_llm(prompt, model) attendue par l'orchestrateur,
    en routant vers le bon provider selon le nom de modèle logique
    (glm / deepseek / qwen). C'est ici, et seulement ici, qu'il faut ajouter
    un nouveau provider si tu en branches un quatrième.
    """
    dispatch: Dict[str, Callable[[str], str]] = {
        "glm": call_glm,
        "deepseek": call_deepseek,
        "qwen": call_qwen,
    }

    def call_llm(prompt: str, model: str) -> str:
        if model not in dispatch:
            raise ValueError(
                f"Modèle '{model}' non supporté. Modèles connus : {list(dispatch)}"
            )
        return dispatch[model](prompt)

    return call_llm


# =========================
# Orchestrateur
# =========================

@dataclass
class DebateResult:
    brief: str
    rounds: Dict[str, List[str]]  # model -> [r0, r1, r2, r3]
    judge: str
    synthesis: str
    meta: Dict[str, Any] = field(default_factory=dict)


class DebateOrchestrator:
    def __init__(
        self,
        call_llm: Callable[[str, str], str],
        max_retries: int = 2,
        delay_between_calls: float = 0.0,
    ):
        """
        call_llm: fonction (prompt: str, model: str) -> str
        """
        self.call_llm = call_llm
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls

    def _call_with_delay(self, prompt: str, model: str) -> str:
        if self.delay_between_calls > 0:
            time.sleep(self.delay_between_calls)
        try:
            return self.call_llm(prompt, model)
        except Exception as e:
            raise LLMCallError(f"Erreur lors de l'appel LLM pour {model}: {e}") from e

    def _round_with_retry(
        self,
        prompt_func: Callable,
        model: str,
        brief: str,
        args: tuple,
        check_format: Callable,
        round_name: str,
    ) -> str:
        for i in range(self.max_retries + 1):
            prompt = prompt_func(brief, *args)
            response = self._call_with_delay(prompt, model)
            if check_format(response):
                return response
            if i < self.max_retries:
                # NOTE (correction) : on ne renvoie plus tout le SKILL_TEXT +
                # tout le prompt d'origine (qui contenait déjà SKILL_TEXT en
                # double), on renvoie juste un rappel court + la réponse
                # fautive, ce qui réduit nettement le coût en tokens des
                # relances.
                fix_prompt = f"""
Ta réponse précédente ne respectait pas le format imposé pour "{round_name}".
Voici les titres de section obligatoires, exactement dans cet esprit
(accents/ponctuation peuvent varier légèrement, la structure doit être là) :

{chr(10).join(f"- {s}" for s in _required_for(round_name))}

Réponds uniquement avec la version corrigée, complète, dans ce format.

Ta réponse précédente était :
{response}
"""
                response = self._call_with_delay(fix_prompt, model)
                if check_format(response):
                    return response
        raise FormatError(
            f"Le modèle {model} n'a pas respecté le format pour {round_name} "
            f"après {self.max_retries + 1} tentatives."
        )

    def run_debate(self, brief: str, models: List[str]) -> Dict[str, List[str]]:
        all_responses: Dict[str, List[str]] = {m: [] for m in models}

        # Round 0
        for model in models:
            r = self._round_with_retry(
                get_prompt_round_0,
                model,
                brief,
                (),
                check_format_round_0,
                "Round 0",
            )
            all_responses[model].append(r)

        # Round 1
        for model in models:
            r = self._round_with_retry(
                get_prompt_round_1,
                model,
                brief,
                (),
                check_format_round_1,
                "Round 1",
            )
            all_responses[model].append(r)

        # Round 2 : chaque modèle lit les Round 1 des AUTRES modèles.
        for model in models:
            others = [all_responses[m][1] for m in models if m != model]
            r = self._round_with_retry(
                get_prompt_round_2,
                model,
                brief,
                (others,),
                check_format_round_2,
                "Round 2",
            )
            all_responses[model].append(r)

        # Round 3 : chaque modèle révise sa PROPRE trajectoire (r1 -> r2).
        for model in models:
            r1 = all_responses[model][1]
            r2 = all_responses[model][2]
            r = self._round_with_retry(
                get_prompt_round_3,
                model,
                brief,
                (r1, r2),
                check_format_round_3,
                "Round 3",
            )
            all_responses[model].append(r)

        return all_responses

    def run_judge(self, brief: str, rounds: Dict[str, List[str]], judge_model: str) -> str:
        prompt = get_prompt_judge(brief, rounds)
        response = self._call_with_delay(prompt, judge_model)
        if not check_format_judge(response):
            fix_prompt = f"""
Ta réponse précédente ne respectait pas le format imposé pour "Juge final".
Voici les titres de section obligatoires :

{chr(10).join(f"- {s}" for s in REQUIRED_JUDGE)}

Réponds uniquement avec la version corrigée, complète, dans ce format.

Ta réponse précédente était :
{response}
"""
            response = self._call_with_delay(fix_prompt, judge_model)
            if not check_format_judge(response):
                raise FormatError("Le juge final n'a pas respecté le format après relance.")
        return response

    def run_synthesis(self, brief: str, judge_response: str, synthesis_model: str) -> str:
        # NOTE (correction) : la version d'origine ignorait le paramètre
        # synthesis_model et appelait toujours le modèle littéral
        # "synthesis-model" (qui n'existe dans aucun dispatch réel) --
        # le résumé final ne pouvait donc jamais fonctionner en pratique.
        prompt = get_prompt_synthesis(brief, judge_response)
        return self._call_with_delay(prompt, synthesis_model)

    def run_full_debate(
        self,
        brief: str,
        models: List[str],
        judge_model: str,
        synthesis_model: Optional[str] = None,
    ) -> DebateResult:
        synthesis_model = synthesis_model or judge_model
        meta: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "models": models,
            "judge_model": judge_model,
            "synthesis_model": synthesis_model,
        }

        rounds = self.run_debate(brief, models)
        judge = self.run_judge(brief, rounds, judge_model)
        synthesis = self.run_synthesis(brief, judge, synthesis_model)

        return DebateResult(
            brief=brief,
            rounds=rounds,
            judge=judge,
            synthesis=synthesis,
            meta=meta,
        )


def _required_for(round_name: str) -> List[str]:
    return {
        "Round 0": REQUIRED_ROUND_0,
        "Round 1": REQUIRED_ROUND_1,
        "Round 2": REQUIRED_ROUND_2,
        "Round 3": REQUIRED_ROUND_3,
        "Juge final": REQUIRED_JUDGE,
    }[round_name]


# =========================
# CLI
# =========================

def load_brief_from_text(brief_text: str) -> str:
    """
    Approche simple : on utilise directement le texte comme brief structuré.
    Pour une vraie structuration automatique, dédie un appel LLM à
    get_prompt_brief_format() avant de lancer le débat.
    """
    return brief_text


def main():
    parser = argparse.ArgumentParser(
        description="Orchestre un débat multi-LLM avec la skill multi-llm-debate-grill-me."
    )
    parser.add_argument("--brief", type=str, default=None, help="Brief du projet en texte libre.")
    parser.add_argument("--brief-file", type=str, default=None, help="Fichier contenant le brief du projet.")
    parser.add_argument(
        "--models",
        type=str,
        default="glm,deepseek,qwen",
        help="Liste de modèles séparés par des VIRGULES (ex: glm,deepseek,qwen).",
    )
    parser.add_argument("--judge", type=str, default="glm", help="Modèle utilisé pour le juge final.")
    parser.add_argument(
        "--synthesis-model", type=str, default=None,
        help="Modèle utilisé pour la synthèse (par défaut = juge).",
    )
    parser.add_argument("--max-retries", type=int, default=2, help="Nombre maximal de relances de format.")
    parser.add_argument("--output-dir", type=str, default="debate_output", help="Dossier de sortie.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="N'appelle aucune API réelle, utilise des réponses simulées (pour tester le pipeline).",
    )

    args = parser.parse_args()

    if args.brief is None and args.brief_file is None:
        parser.error("Tu dois fournir --brief ou --brief-file.")
    elif args.brief is not None:
        brief_text = args.brief
    else:
        brief_path = Path(args.brief_file)
        if not brief_path.exists():
            parser.error(f"Fichier de brief inexistant : {args.brief_file}")
        brief_text = brief_path.read_text(encoding="utf-8")

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if len(models) < 2:
        parser.error("Tu dois fournir au moins 2 modèles (3 recommandé pour un vrai consensus).")

    if args.dry_run:
        _stub_by_round = {
            "Round 0 (cadrage silencieux)": "\n".join(REQUIRED_ROUND_0) + "\n- x",
            "Round 1 (position initiale)": "\n".join(REQUIRED_ROUND_1) + "\n- x",
            "Round 2 (lecture croisée)": "\n".join(REQUIRED_ROUND_2) + "\n- x",
            "Round 3 (révision finale)": "\n".join(REQUIRED_ROUND_3) + "\n- x",
            "Tu es le juge final": "\n".join(REQUIRED_JUDGE) + "\n- x",
        }

        def call_llm(prompt: str, model: str) -> str:
            for marker, stub in _stub_by_round.items():
                if marker in prompt:
                    return f"{stub}\n[Réponse simulée pour {model}]"
            return f"[Réponse simulée (synthèse) pour {model}]"
    else:
        call_llm = make_call_llm()

    orchestrator = DebateOrchestrator(
        call_llm=call_llm,
        max_retries=args.max_retries,
        delay_between_calls=0.0,
    )

    brief = load_brief_from_text(brief_text)

    print("Début du débat multi-LLM...")
    try:
        result = orchestrator.run_full_debate(
            brief=brief,
            models=models,
            judge_model=args.judge,
            synthesis_model=args.synthesis_model,
        )
    except DebateError as e:
        print(f"Erreur dans le débat : {e}")
        sys.exit(1)

    print("Débat terminé. Synthèse :")
    print(result.synthesis)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "brief.txt").write_text(brief, encoding="utf-8")
    (output_dir / "judge.txt").write_text(result.judge, encoding="utf-8")
    (output_dir / "synthesis.txt").write_text(result.synthesis, encoding="utf-8")
    (output_dir / "rounds.json").write_text(
        json.dumps(result.rounds, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "meta.json").write_text(
        json.dumps(result.meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Résultats enregistrés dans {output_dir}/")


if __name__ == "__main__":
    main()
