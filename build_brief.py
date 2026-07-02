#!/usr/bin/env python3
"""
build_brief.py — Assistant interactif pour construire un brief.txt riche,
destiné à être ensuite passé à debate_cli.py --brief-file.

Usage :
    python build_brief.py
    python build_brief.py --output mon-brief.txt
    python build_brief.py --enrich --enrich-model glm
    python build_brief.py --from-json brief.json --output brief.txt
    python build_brief.py --then-debate --models glm,deepseek,qwen --judge glm
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# =========================
# Questions du wizard
# =========================

@dataclass
class Question:
    key: str
    prompt: str
    required: bool = True
    multiline: bool = False
    hint: Optional[str] = None

QUESTIONS: List[Question] = [
    Question(
        key="nature",
        prompt="Quelle est la nature de ton projet ?",
        required=True,
        hint="ex: application web, outil CLI, script d'automatisation, librairie, API...",
    ),
    Question(
        key="objectif",
        prompt="Quel est l'objectif principal ? Que doit accomplir ce projet concrètement ?",
        required=True,
        multiline=True,
    ),
    Question(
        key="utilisateurs",
        prompt="Qui va utiliser ce projet ?",
        required=True,
        hint="ex: toi seul, une petite équipe, le grand public, des développeurs...",
    ),
    Question(
        key="contraintes",
        prompt="Quelles contraintes dois-tu respecter ?",
        required=False,
        multiline=True,
        hint="ex: délai, budget, stack imposée, compatibilité, hébergement...",
    ),
    Question(
        key="choix_faits",
        prompt="Quels choix as-tu déjà faits, et pourquoi ?",
        required=False,
        multiline=True,
        hint="ex: langage, framework, architecture, base de données...",
    ),
    Question(
        key="a_challenger",
        prompt="Qu'est-ce que tu veux spécifiquement voir challengé par le débat ?",
        required=True,
        multiline=True,
        hint="ex: la faisabilité technique, les failles de sécurité, le choix d'architecture, la scalabilité...",
    ),
    Question(
        key="risques_connus",
        prompt="Connais-tu déjà des risques ou points faibles de ce plan ?",
        required=False,
        multiline=True,
    ),
    Question(
        key="succes",
        prompt="À quoi ressemblerait un succès pour ce projet ?",
        required=False,
    ),
]

# =========================
# Saisie interactive
# =========================

def ask_single_line(prompt: str, required: bool) -> str:
    while True:
        answer = input(f"{prompt}\n> ").strip()
        if answer or not required:
            return answer
        print("  (réponse obligatoire, réessaie)")

def ask_multiline(prompt: str, required: bool) -> str:
    print(f"{prompt}")
    print("  (plusieurs lignes possibles, termine par une ligne vide)")
    lines: List[str] = []
    while True:
        line = input("> ")
        if line == "":
            if lines or not required:
                break
            print("  (réponse obligatoire, réessaie)")
            continue
        lines.append(line)
    return "\n".join(lines).strip()

def run_wizard() -> Dict[str, str]:
    print("=" * 60)
    print("  Assistant de construction de brief — multi-llm-debate-cli")
    print("=" * 60)
    print()
    answers: Dict[str, str] = {}
    for i, q in enumerate(QUESTIONS, start=1):
        marker = "*" if q.required else " "
        print(f"[{i}/{len(QUESTIONS)}]{marker} {q.hint or ''}".rstrip())
        if q.multiline:
            answers[q.key] = ask_multiline(q.prompt, q.required)
        else:
            answers[q.key] = ask_single_line(q.prompt, q.required)
        print()
    return answers

# =========================
# Construction du brief.txt
# =========================

SECTION_TITLES = {
    "nature": "Sujet",
    "objectif": "Objectif",
    "utilisateurs": "Utilisateurs cibles",
    "contraintes": "Contraintes",
    "choix_faits": "Choix déjà faits",
    "a_challenger": "Ce que tu veux challenger",
    "risques_connus": "Risques déjà identifiés",
    "succes": "Critère de succès",
}

def build_brief_text(answers: Dict[str, str]) -> str:
    lines = ["# Brief du projet", ""]
    for key, title in SECTION_TITLES.items():
        value = answers.get(key, "").strip()
        if not value:
            continue
        lines.append(f"## {title}")
        lines.append("")
        lines.append(value)
        lines.append("")
    return "\n".join(lines).strip() + "\n"

# =========================
# Vérification de structure
# =========================

REQUIRED_SECTIONS = ["## Sujet", "## Objectif", "## Utilisateurs cibles", "## Ce que tu veux challenger"]

def check_brief_structure(brief_text: str) -> bool:
    """Vérifie que les sections principales sont présentes."""
    missing = [s for s in REQUIRED_SECTIONS if s not in brief_text]
    if missing:
        print("⚠️  Le brief enrichi ne contient pas toutes les sections attendues :")
        for m in missing:
            print(f"   - {m} manquant")
        return False
    return True

# =========================
# Enrichissement optionnel via LLM
# =========================

def enrich_with_llm(brief_text: str, model: str, debate_cli_path: Path) -> str:
    """
    Passe le brief structuré à un LLM pour le reformuler en un texte plus dense,
    sans inventer de faits. Réutilise le routage de debate_cli.py.
    """
    # Ajout du chemin du module pour l'import
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("debate_cli", debate_cli_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Impossible de charger debate_cli depuis {debate_cli_path}")
    debate_cli = importlib.util.module_from_spec(spec)
    sys.modules["debate_cli"] = debate_cli
    spec.loader.exec_module(debate_cli)

    call_llm = debate_cli.make_call_llm()

    prompt = f"""
Voici un brief de projet rempli par un utilisateur, section par section.
Certaines sections sont courtes ou télégraphiques.

Réécris ce brief en un texte plus dense, plus clair et plus précis, en
gardant exactement la même structure de sections (mêmes titres, même
ordre). N'invente aucun fait, aucune contrainte, aucun choix qui n'est pas
déjà présent dans le texte d'origine : tu peux reformuler, préciser le
vocabulaire, expliciter des implications évidentes, mais pas ajouter
d'information nouvelle.

Brief d'origine :

{brief_text}
"""
    return call_llm(prompt, model)

# =========================
# Validation des modèles (liste connue)
# =========================

KNOWN_MODELS = {"glm", "deepseek", "qwen"}

def validate_models(models_str: str) -> List[str]:
    models = [m.strip() for m in models_str.split(",") if m.strip()]
    unknown = [m for m in models if m not in KNOWN_MODELS]
    if unknown:
        print(f"⚠️  Modèles inconnus : {', '.join(unknown)}")
        print(f"   Modèles supportés : {', '.join(sorted(KNOWN_MODELS))}")
        response = input("   Continuer quand même ? (o/N) ").strip().lower()
        if response != "o":
            print("Annulation.")
            sys.exit(1)
    return models

# =========================
# CLI
# =========================

def main():
    parser = argparse.ArgumentParser(
        description="Construit un brief.txt riche pour multi-llm-debate-cli, via un wizard interactif."
    )
    parser.add_argument("--output", type=str, default="brief.txt", help="Fichier de sortie pour le brief texte.")
    parser.add_argument(
        "--save-json", type=str, default=None,
        help="Chemin où sauvegarder les réponses brutes en JSON (par défaut : <output>.json).",
    )
    parser.add_argument(
        "--from-json", type=str, default=None,
        help="Relit des réponses déjà enregistrées au lieu de lancer le wizard interactif.",
    )
    parser.add_argument(
        "--enrich", action="store_true",
        help="Envoie le brief à un LLM pour le reformuler en un texte plus dense avant de l'enregistrer.",
    )
    parser.add_argument(
        "--enrich-model", type=str, default="glm",
        help="Modèle utilisé pour l'enrichissement (glm, deepseek, qwen). Nécessite la clé API correspondante.",
    )
    parser.add_argument(
        "--debate-cli-path", type=str, default="debate_cli.py",
        help="Chemin vers debate_cli.py (pour l'enrichissement et --then-debate).",
    )
    parser.add_argument(
        "--then-debate", action="store_true",
        help="Une fois le brief généré, enchaîne automatiquement sur debate_cli.py --brief-file.",
    )
    parser.add_argument("--models", type=str, default="glm,deepseek,qwen", help="Modèles pour --then-debate.")
    parser.add_argument("--judge", type=str, default="glm", help="Juge pour --then-debate.")
    parser.add_argument("--dry-run", action="store_true", help="Passé tel quel à debate_cli.py si --then-debate.")

    args = parser.parse_args()

    # Vérifier que le chemin vers debate_cli.py existe
    debate_cli_path = Path(args.debate_cli_path)
    if not debate_cli_path.exists():
        parser.error(f"Fichier debate_cli.py introuvable : {args.debate_cli_path}")

    # Chargement des réponses
    if args.from_json:
        json_path = Path(args.from_json)
        if not json_path.exists():
            parser.error(f"Fichier JSON introuvable : {args.from_json}")
        answers = json.loads(json_path.read_text(encoding="utf-8"))
    else:
        answers = run_wizard()

    brief_text = build_brief_text(answers)

    # Enrichissement optionnel
    if args.enrich:
        print("Enrichissement du brief via LLM en cours...")
        enriched = enrich_with_llm(brief_text, args.enrich_model, debate_cli_path)
        # Vérification de la structure
        if check_brief_structure(enriched):
            brief_text = enriched
            print("✅ Enrichissement réussi et structure valide.")
        else:
            print("❌ L'enrichissement a produit un brief avec des sections manquantes.")
            print("   Conservation du brief d'origine.")
            # On garde brief_text inchangé

    # Sauvegarde
    output_path = Path(args.output)
    output_path.write_text(brief_text, encoding="utf-8")
    print(f"Brief enregistré dans {output_path}")

    json_path = Path(args.save_json) if args.save_json else output_path.with_suffix(".json")
    json_path.write_text(
        json.dumps({**answers, "_generated_at": datetime.now().isoformat()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Réponses brutes enregistrées dans {json_path}")

    # Enchaînement vers le débat
    if args.then_debate:
        # Valider les modèles
        models_list = validate_models(args.models)
        if args.judge not in KNOWN_MODELS:
            print(f"⚠️  Le juge '{args.judge}' n'est pas dans la liste connue ({', '.join(KNOWN_MODELS)}).")
            response = input("   Continuer quand même ? (o/N) ").strip().lower()
            if response != "o":
                print("Annulation.")
                sys.exit(1)

        print("\nLancement du débat multi-LLM avec ce brief...\n")
        cmd = [
            sys.executable, str(debate_cli_path),
            "--brief-file", str(output_path),
            "--models", args.models,
            "--judge", args.judge,
        ]
        if args.dry_run:
            cmd.append("--dry-run")

        try:
            subprocess.run(cmd, check=True)
            print("\n✅ Débat terminé avec succès.")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Le débat a échoué avec le code d'erreur {e.returncode}.")
            print("   Vérifie les logs ci-dessus pour plus de détails.")
            sys.exit(e.returncode)

if __name__ == "__main__":
    main()
