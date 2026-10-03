#!/usr/bin/env python3
"""
daily_companion.py — Daily cognitive companion

Opens an Anthropic Messages API conversation grounded in today's unified
daily reading. Every response is governed by the day's cognitive frame:

  · Purpose position  — the SM governing number shapes the conversation's orientation
  · Domain            — shapes HOW reasoning unfolds
  · Value             — shapes WHAT is honored in every response
  · Stage             — places the conversation inside a developmental arc
  · Process functions — active cognitive capacities for the day

Commands during conversation:
  /reading   — display today's full frame
  /refresh   — recompute reading for now (new hour)
  /clear     — start a new conversation (keep the frame)
  /quit      — exit

Usage:
  python daily_companion.py
  python daily_companion.py --date 2026-10-07
  python daily_companion.py --org assessments/Donation_Station_HP_20260916_113000.json
  python daily_companion.py --model claude-opus-5-5
  python daily_companion.py --no-stream
"""

import argparse
import datetime
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

import unified_daily as ud
from suprememath import Lexicon, DEFAULT_LEXICON_PATH

SEP  = "─" * 66
DSEP = "═" * 66

# Domain → reasoning instruction
DOMAIN_INSTRUCTIONS = {
    "Quantity":                  "Reason with precision about amounts, magnitudes, and measurable relationships. Favor the concrete and countable.",
    "Relationships":             "Center connections, dependencies, and dynamics between things. How do they affect each other? What holds them together or apart?",
    "Representation":            "Attend to how things are named, modeled, and symbolized. The map shapes what we see of the territory.",
    "Abstraction/Generalization": "Find the general principle behind the specific instance. Draw out the underlying structure. What is true across cases?",
    "Logic/Proof":               "Reason in deductive chains. State necessary conditions. Distinguish what follows necessarily from what merely tends to follow.",
    "Precision":                 "Disambiguate carefully. Name things exactly. Resist conflation. One word, one meaning.",
}

# Value → honoring instruction
VALUE_INSTRUCTIONS = {
    "INTEGRITY":               "Hold coherence between what is stated and what is enacted. Surface contradictions gently.",
    "DIGNITY":                 "Honor the worth of every person, idea, and effort brought into this conversation.",
    "DISCERNMENT":             "Distinguish carefully. Do not conflate similar things. Name the difference when it matters.",
    "THE STRUGGLE":            "Acknowledge difficulty honestly. Do not smooth over what is genuinely hard. Safeguard the person in the difficulty.",
    "GOOD ANCESTORSHIP":       "Weigh every response by what it leaves for future selves. What inheritance does this choice create?",
}


def build_system_prompt(reading):
    """Build a system prompt that encodes the day's full cognitive frame."""
    sm      = reading["sm"]
    process = reading["process"]
    domain  = reading["domain"]
    value   = reading["value"]
    stage   = reading["stage"]
    axiom   = reading["axiom"]

    pur = sm["purpose"]
    att = sm["attention"]
    itn = sm["intention"]

    domain_name = domain["name"] if domain else "—"
    value_name  = value["name"]  if value  else "—"
    stage_name  = stage["name"]  if stage  else "—"
    stage_num   = stage["number"] if stage else "—"
    stage_etym  = stage["etymology"] if stage else ""

    process_list = "\n".join(f"  · {p['name']}" for p in process)

    domain_instr = DOMAIN_INSTRUCTIONS.get(domain_name, "")
    value_instr  = VALUE_INSTRUCTIONS.get(value_name, "")

    aligned_note = ""
    conv = sm["secondary"]["convergence"]
    if conv["aligned"]:
        aligned_note = "\n\nToday is ✦ ALIGNED — the convergence equals 6 (Equality). This is a day of rare balance. Attend to equity and mutual recognition in every exchange."

    axiom_note = ""
    if axiom:
        dim = axiom["dimension"]
        axiom_note = (
            f"\n\nORGANIZATIONAL CONTEXT ({axiom['organization']})\n"
            f"Governing dimension P{dim['position']}: {dim['name']} — "
            f"{dim['average']:.2f} [{dim['level']}]\n"
            f"Aggregate health: {axiom['aggregate_score']} [{axiom['aggregate_level']}]"
        )

    return f"""You are a daily cognitive companion operating within today's governing frame.

DATE: {sm['date']}
FRACTION CALENDAR: {att['number']} (Attention) · {itn['number']} (Intention) · {pur['number']} (Purpose)
PURPOSE: {pur['number']} — {pur['name']}  ← governing position

COGNITIVE FRAME
───────────────
Domain in frame:    {domain_name}
Value governing:    {value_name}
Stage:              {stage_num}/16 — {stage_name}  [{stage_etym}]

Active process functions:
{process_list}

GOVERNING INSTRUCTIONS
──────────────────────
Domain  ({domain_name}): {domain_instr}

Value   ({value_name}): {value_instr}

Stage   ({stage_name}): You are in stage {stage_num} of 16 in the self-determination cycle. The etymology "{stage_etym}" is the root of this moment's developmental work. Let it inform how you hold the conversation.{aligned_note}{axiom_note}

OPERATING PRINCIPLES
────────────────────
1. Do not announce the frame on every response — embody it.
2. When a question touches the governing domain directly, go deep.
3. When a choice or recommendation arises, run it through the governing value before offering it.
4. Be brief when the frame calls for precision. Be expansive when it calls for relationships.
5. You are not a generic assistant today — you are this day's companion, shaped by this day's frame."""


def format_frame_display(reading):
    """Return a compact frame summary for the terminal header."""
    sm      = reading["sm"]
    process = reading["process"]
    domain  = reading["domain"]
    value   = reading["value"]
    stage   = reading["stage"]
    axiom   = reading["axiom"]

    pur  = sm["purpose"]
    moon = sm["moon"]
    conv = sm["secondary"]["convergence"]

    aligned_mark = "  ✦ ALIGNED" if conv["aligned"] else ""

    lines = [
        f"\n{DSEP}",
        f"  DAILY COMPANION  ·  {sm['date']}  {sm['time']}",
        DSEP,
        f"\n  {moon['emoji']}  Purpose {pur['number']} — {pur['name']}{aligned_mark}",
    ]

    if domain:
        lines.append(f"  Domain    →  {domain['name']}")
    if value:
        lines.append(f"  Value     →  {value['name']}")
    if stage:
        lines.append(f"  Stage     →  {stage['number']}/16 · {stage['name']}  [{stage['etymology']}]")

    if process:
        lines.append(f"\n  Process functions active:")
        for p in process:
            lines.append(f"    · {p['name']}")

    if axiom:
        dim = axiom["dimension"]
        lines.append(f"\n  AXIOM  P{dim['position']} {dim['name']}:  {dim['average']:.2f} [{dim['level']}]")

    lines.append(f"\n  Commands: /reading  /refresh  /clear  /quit")
    lines.append(DSEP)

    return "\n".join(lines)


def run_companion(reading, model, stream, assessment_path=None, dt=None):
    """Main conversation loop."""
    try:
        import anthropic
    except ImportError:
        print("\n  anthropic package required. Install with: pip install anthropic\n")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n  ANTHROPIC_API_KEY not set.")
        print("  Export it: export ANTHROPIC_API_KEY=sk-ant-...\n")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(format_frame_display(reading))
    print()

    messages  = []
    system_prompt = build_system_prompt(reading)

    # readline for better input experience
    try:
        import readline
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass

    while True:
        try:
            user_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Until tomorrow.\n")
            break

        if not user_input:
            continue

        # Commands
        if user_input.lower() == "/quit":
            print("\n  Until tomorrow.\n")
            break

        if user_input.lower() == "/reading":
            print(format_frame_display(reading))
            continue

        if user_input.lower() == "/refresh":
            now = datetime.datetime.now()
            lexicon = Lexicon(DEFAULT_LEXICON_PATH)
            reading = ud.compute_unified(now, lexicon=lexicon, assessment_path=assessment_path)
            system_prompt = build_system_prompt(reading)
            print(format_frame_display(reading))
            print("  Frame refreshed.\n")
            continue

        if user_input.lower() == "/clear":
            messages = []
            print(f"\n  {SEP[2:]}")
            print(f"  Conversation cleared. Frame intact.")
            print(f"  {SEP[2:]}\n")
            continue

        messages.append({"role": "user", "content": user_input})

        print(f"\n  Companion: ", end="", flush=True)

        if stream:
            full_response = ""
            with client.messages.stream(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            ) as s:
                for text in s.text_stream:
                    print(text, end="", flush=True)
                    full_response += text
            print("\n")
            messages.append({"role": "assistant", "content": full_response})
        else:
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            )
            reply = response.content[0].text
            print(reply)
            print()
            messages.append({"role": "assistant", "content": reply})


def main():
    parser = argparse.ArgumentParser(
        description="Daily Companion — Anthropic conversation grounded in today's cognitive frame",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python daily_companion.py\n"
            "  python daily_companion.py --date 2026-10-07\n"
            "  python daily_companion.py --org assessments/Donation_Station_HP_20260916_113000.json\n"
            "  python daily_companion.py --model claude-opus-5-5\n"
            "  python daily_companion.py --no-stream"
        ),
    )
    parser.add_argument("--date",      metavar="YYYY-MM-DD", help="Date for the reading (default: today)")
    parser.add_argument("--hour",      type=int, metavar="0-23", help="Hour 0-23 (default: now)")
    parser.add_argument("--org",       metavar="FILE", help="AXIOM assessment JSON for organizational context")
    parser.add_argument("--model",     default="claude-sonnet-5-5", metavar="MODEL", help="Anthropic model ID (default: claude-sonnet-5-5)")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    args = parser.parse_args()

    now = datetime.datetime.now()

    if args.date:
        try:
            d = datetime.date.fromisoformat(args.date)
        except ValueError:
            print(f"Invalid date {args.date!r}. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        d = now.date()

    hour = args.hour if args.hour is not None else now.hour
    dt   = datetime.datetime(d.year, d.month, d.day, hour, now.minute)

    lexicon = Lexicon(DEFAULT_LEXICON_PATH)
    reading = ud.compute_unified(dt, lexicon=lexicon, assessment_path=args.org)

    run_companion(
        reading,
        model=args.model,
        stream=not args.no_stream,
        assessment_path=args.org,
        dt=dt,
    )


if __name__ == "__main__":
    main()
