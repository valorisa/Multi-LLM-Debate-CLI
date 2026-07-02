# Multi-LLM Debate CLI

> A beginner-friendly command-line tool that makes several AI language models
> **debate each other** about your project idea before you commit to it —
> instead of asking a single model and hoping for the best.

## Table of contents

- [Why this tool exists](#why-this-tool-exists)
- [The core idea in plain language](#the-core-idea-in-plain-language)
- [What "debate" actually means here](#what-debate-actually-means-here)
- [Why three models instead of one or two](#why-three-models-instead-of-one-or-two)
- [What you need before starting](#what-you-need-before-starting)
- [Installation, step by step](#installation-step-by-step)
- [Getting your API keys](#getting-your-api-keys)
- [Your first run (safe, no API calls)](#your-first-run-safe-no-api-calls)
- [Your first real debate](#your-first-real-debate)
- [Understanding the five phases of a debate](#understanding-the-five-phases-of-a-debate)
- [Reading the output files](#reading-the-output-files)
- [All command-line options](#all-command-line-options)
- [Choosing your models wisely](#choosing-your-models-wisely)
- [Adding a fourth model or provider](#adding-a-fourth-model-or-provider)
- [Cost and rate-limit awareness](#cost-and-rate-limit-awareness)
- [Troubleshooting](#troubleshooting)
- [Frequently asked questions](#frequently-asked-questions)
- [Related project: the chat-based version of this workflow](#related-project-the-chat-based-version-of-this-workflow)
- [License](#license)

## Why this tool exists

If you have ever asked a single AI model "is this a good plan?", you already
know the problem: it tends to be agreeable. It rarely tells you "this idea
has a fatal flaw" unless you specifically push it to. Different models also
have different blind spots — one might be great at spotting security issues
and terrible at questioning your assumptions, another might be the opposite.

This tool exists to remove the guesswork from getting a **second, third, and
fourth opinion** on a project idea, an architecture choice, or a design
decision — automatically, in a structured and repeatable way, instead of you
manually copy-pasting text between browser tabs.

> **Note for absolute beginners**
> You do not need to know how to code to use this tool. You need to be
> comfortable typing a few commands in a terminal, and to have (or be
> willing to create) free or paid accounts with the AI providers you want to
> use. Every step below is explained as if it were your first time.

## The core idea in plain language

Imagine you have an idea for a project. Instead of asking one friend for
feedback, you gather three friends who don't know each other's opinions yet,
and you ask each of them independently:

1. What could go wrong with this idea?
2. What am I not seeing?
3. What would you change?

Then you let them read each other's answers and react — "I agree with this
point, I disagree with that one, here is why." Finally, you ask a fourth,
neutral friend to read the whole conversation and give you a final verdict.

That is exactly what this tool automates, except your three (or more)
"friends" are AI language models — for example GLM, DeepSeek, and Qwen — and
the fourth "friend" who gives the final verdict is called the **judge**.

## What "debate" actually means here

A common (and weaker) way to combine several AI models is to **chain** them:
you ask model A, then you paste model A's answer into model B and ask it to
comment, then you paste model B's answer into model C. This sounds
reasonable, but it has a hidden flaw: whatever mistake or blind spot model A
introduces early on tends to **propagate and get amplified** down the chain,
because each model only ever sees the previous model's framing of the
problem, never the original problem itself.

This tool avoids that trap by following a **five-phase protocol** where
every model always has access to your original brief, not just what the
previous model said about it. The phases are explained in detail further
down, but the short version is:

- **Phase 0** — every model quietly maps out the problem on its own first
  (branches, dependencies, ambiguities) before saying anything out loud.
- **Phase 1** — every model gives its first, fully independent opinion.
- **Phase 2** — every model reads the *other* models' first opinions and
  reacts: what it keeps, what it corrects, what it rejects.
- **Phase 3** — every model revises its own position one last time.
- **Judge phase** — a separate model reads everything and delivers a final,
  arbitrated verdict.

## Why three models instead of one or two

- **One model** gives you an opinion, not a stress-test.
- **Two models** give you a second opinion, which is already useful, but you
  cannot tell whether a disagreement means "one of them is wrong" or "this
  is genuinely ambiguous."
- **Three models** let you start seeing patterns: if two out of three flag
  the same risk, that risk is probably real. If all three disagree, you have
  found a genuinely open question worth thinking about yourself.

You can use more than three if you want extra coverage, but keep in mind
that cost and waiting time increase with every extra model, and beyond three
or four the extra insight you gain usually shrinks fast.

## What you need before starting

- A computer with **Python 3.10 or newer** installed.
- A terminal (on Windows: PowerShell; on Android/Termux: the Termux shell;
  on macOS/Linux: your usual terminal).
- **Git**, to download (clone) this repository.
- Accounts and API keys for the AI providers you want to use — at least two,
  ideally three. This project ships ready-to-use support for:
  - **GLM** (via [Z.AI](https://www.z.ai))
  - **DeepSeek** (via the [DeepSeek platform](https://platform.deepseek.com))
  - **Qwen** (via [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com))

> **Note**
> You do not need all three. Two is the strict minimum the tool accepts, but
> three is strongly recommended for the reasons explained above.

## Installation, step by step

1. **Clone the repository** (download a copy onto your machine):

   ```bash
   git clone https://github.com/valorisa/multi-llm-debate-cli.git
   cd multi-llm-debate-cli
   ```

2. **Create a virtual environment** (a self-contained Python installation
   just for this project, so it doesn't interfere with anything else on your
   machine). This step is optional but strongly recommended:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # on Windows PowerShell: .venv\Scripts\Activate.ps1
   ```

3. **Install the dependencies** (the external libraries this tool needs to
   talk to each AI provider):

   ```bash
   pip install -r requirements.txt
   ```

4. **Create your own `.env` file** from the provided template, and fill in
   the API keys you have (see the next section if you don't have them yet):

   ```bash
   cp .env.example .env
   ```

   Then open `.env` in any text editor and paste your keys after the `=`
   signs. This file is already excluded from Git (see `.gitignore`), so your
   keys will never accidentally end up on GitHub.

## Getting your API keys

You only need keys for the providers you actually plan to use.

- **Z.AI (for GLM)**: create an account at
  [z.ai](https://www.z.ai), then generate an API key from your account
  dashboard. Set it as `ZAI_API_KEY` in your `.env` file.
- **DeepSeek**: create an account at
  [platform.deepseek.com](https://platform.deepseek.com), then generate an
  API key. Set it as `DEEPSEEK_API_KEY` in your `.env` file.
- **Qwen (DashScope)**: create an account at
  [Alibaba Cloud DashScope](https://dashscope.console.aliyun.com), then
  generate an API key. Set it as `QWEN_API_KEY` in your `.env` file.

> **Security note**
> Treat these keys like passwords. Never paste them directly in a chat, a
> screenshot, or a public GitHub issue. If you ever suspect a key has
> leaked, revoke it immediately from the provider's dashboard and generate a
> new one.

## Your first run (safe, no API calls)

Before spending any API credits, run the tool in **dry-run mode**. This
simulates the entire five-phase protocol with fake responses, so you can
confirm everything is installed correctly and understand what the output
looks like:

```bash
python debate_cli.py \
  --brief "I want to build a small CLI tool that converts CSV files to JSON." \
  --models glm,deepseek,qwen \
  --judge glm \
  --dry-run
```

If this finishes with a message like `Results saved in debate_output/`,
your installation is working correctly.

## Your first real debate

Once your `.env` file contains valid API keys, remove `--dry-run` and run
the same command again — this time it will make real calls to each
provider:

```bash
python debate_cli.py \
  --brief "I want to build a small CLI tool that converts CSV files to JSON." \
  --models glm,deepseek,qwen \
  --judge glm
```

> **Tip for a better debate**
> The more detail you put in `--brief`, the better the debate. A one-line
> idea works, but a short paragraph covering the goal, the target users, the
> constraints, and what you specifically want challenged will produce a much
> more useful debate. You can also put a longer brief in a text file and
> pass it with `--brief-file my-brief.txt` instead of `--brief`.

## Understanding the five phases of a debate

| Phase | Name | What happens | Who sees what |
|---|---|---|---|
| 0 | Silent framing | Each model privately maps decision branches, dependencies, and ambiguities in your brief. | Each model only sees your brief. |
| 1 | Initial position | Each model gives its first full, independent analysis: strengths, weaknesses, critical risks. | Each model only sees your brief (not the other models' answers yet). |
| 2 | Cross-reading | Each model reads the *other* models' Phase 1 answers and reacts: what it keeps, corrects, or rejects. | Each model sees your brief + the other models' Phase 1 answers. |
| 3 | Final revision | Each model produces a consolidated, updated position after the cross-reading. | Each model sees its own Phase 1 and Phase 2 answers. |
| Judge | Arbitration | A separate (or the same) model reads every model's full trajectory and delivers a final, reasoned verdict. | The judge sees everything from every model. |

After the judge phase, the tool automatically asks one more model to turn
the judge's verdict into a short, clean **synthesis document** — the part
you will actually want to read first.

## Reading the output files

Every run creates a folder (`debate_output/` by default, configurable with
`--output-dir`) containing:

- `brief.txt` — the exact brief that was used for this run, so you always
  know what was debated.
- `rounds.json` — every model's answer at every phase, in order
  (`[Phase 0, Phase 1, Phase 2, Phase 3]`), useful if you want to read the
  full reasoning trail.
- `judge.txt` — the judge model's full arbitration.
- `synthesis.txt` — the short, readable final summary. **Start here.**
- `meta.json` — technical metadata about the run (timestamp, which models
  were used, which model judged, which model synthesized).

## All command-line options

| Option | Required | Default | Meaning |
|---|---|---|---|
| `--brief` | one of `--brief` / `--brief-file` | — | Your project idea, written directly on the command line. |
| `--brief-file` | one of `--brief` / `--brief-file` | — | Path to a text file containing your project idea. |
| `--models` | no | `glm,deepseek,qwen` | Comma-separated list of models to debate with. |
| `--judge` | no | `glm` | Which model arbitrates at the end. |
| `--synthesis-model` | no | same as `--judge` | Which model writes the final short summary. |
| `--max-retries` | no | `2` | How many times to ask a model to fix its answer if it doesn't follow the expected structure. |
| `--output-dir` | no | `debate_output` | Where to save the result files. |
| `--dry-run` | no | off | Simulate the whole run with fake answers, without calling any real API. |

## Choosing your models wisely

A good rule of thumb, inspired by real multi-agent review practices: give
each model a distinct **role** rather than asking all three the exact same
generic question. For example:

- One model focused on **architecture and structure** — is the plan
  well-organized, are the pieces in the right order?
- One model focused on **implementation feasibility** — can this actually be
  built with the proposed stack, in the proposed timeframe?
- One model focused on **critical review** — security concerns, missing
  edge cases, untested assumptions.

You steer this by how you phrase your `--brief`: explicitly ask, at the end
of your brief, for each of these angles to be covered, and the models will
naturally lean into them during the debate.

For the **judge**, prefer a model that was **not** one of the three
debaters if you can afford it — a model with no stake in defending its own
earlier answer tends to arbitrate more fairly. If you only have access to
one strong model overall, reusing it as judge is still far better than
skipping the judge phase entirely.

## Adding a fourth model or provider

The routing between a model's short name (`"glm"`, `"deepseek"`, `"qwen"`)
and the actual API call lives in a single place: the `make_call_llm()`
function near the top of `debate_cli.py`. To add a new provider:

1. Write a `call_<provider>(prompt: str) -> str` function, following the
   pattern of the existing `call_glm`, `call_deepseek`, and `call_qwen`
   functions.
2. Add your API key retrieval (`get_<provider>_api_key()`), reading from the
   environment the same way the existing ones do.
3. Register your function in the `dispatch` dictionary inside
   `make_call_llm()`.
4. Pass your provider's short name to `--models` and, optionally, `--judge`.

## Cost and rate-limit awareness

A single full debate with 3 models makes roughly:

- 3 calls for Phase 0
- 3 calls for Phase 1
- 3 calls for Phase 2
- 3 calls for Phase 3
- 1 call for the judge
- 1 call for the synthesis

That is **14 API calls minimum** per debate, more if any model's answer
needs a retry to match the expected format. For a simple idea, this can be
disproportionate — always run `--dry-run` first, and reserve real debates
for decisions that actually matter enough to justify the cost and the wait.

## Troubleshooting

- **`ZAI_API_KEY manquante dans l'environnement` / "missing from the
  environment"** — your `.env` file either doesn't exist yet, wasn't filled
  in, or wasn't loaded. Make sure you copied `.env.example` to `.env` and
  that the key is actually pasted in.
- **`Le modèle X n'a pas respecté le format... après N tentatives` / "did not
  follow the expected format after N attempts"** — this means a model kept
  giving free-form answers instead of the structured format the tool
  expects, even after being asked to correct itself. Try increasing
  `--max-retries`, or switch that role to a different, more instruction-
  following model.
- **`Modèle 'x' non supporté` / "not supported"** — you passed a model name
  in `--models` or `--judge` that isn't registered in `make_call_llm()`.
  Double-check spelling (`glm`, `deepseek`, `qwen`), or add support for it
  (see the section above on adding a new provider).
- **Nothing happens for a long time** — this is normal, especially with 3
  models and 4 phases; a full debate can take several minutes depending on
  each provider's response time.

## Frequently asked questions

**Do I need to know how the debate protocol works to use this tool?**
No. The tool handles the entire protocol for you. Reading the "Understanding
the five phases" section above will help you interpret the output better,
but it is not required to run a debate.

**Can I use this with only two models?**
Yes, two is the technical minimum. Three is recommended because it enables
a basic form of consensus ("2 out of 3 agree this is a real risk").

**Can I use this without any coding experience?**
Yes. You do not need to write or modify any Python code to use this tool
day-to-day — only to add a new AI provider, which is optional.

**Is this the same as chatting with three browser tabs open?**
It automates and structures what you would otherwise have to do manually by
copy-pasting between browser tabs — with the added benefit that the format
of each answer is automatically checked and, if needed, the model is asked
to correct itself.

## Related project: the chat-based version of this workflow

If you don't want to set up API keys and prefer using the free web chat
interfaces of GLM, DeepSeek, Claude, Qwen, and similar tools by hand, the
same debate protocol is also available as a portable **skill file** you can
paste directly into any chat: see the
[`multi-llm-debate-grill-me`](https://github.com/valorisa/Claude-Skills/tree/main/skills/multi-llm-debate-grill-me)
skill in the [Claude-Skills](https://github.com/valorisa/Claude-Skills)
repository. This CLI tool follows the exact same protocol, just automated
end to end instead of copy-pasted by hand.

## License

This project is released under the [MIT License](./LICENSE) — you are free
to use, modify, and redistribute it, including for commercial purposes, as
long as you keep the copyright notice.

## A closing note on what this tool is (and isn't)

This tool helps you **stress-test the internal coherence** of a plan or a
design by exposing it to several independent, critical readings. It does
not replace real testing, a real security audit, or real user feedback. A
plan can survive a debate perfectly and still fail in the real world — but a
plan that survives a genuine multi-model debate is, on average, a much
better starting point than one that was never challenged at all.
