"""
validate_scout.py — Run on raw HTML before using any SCOUT output.
Checks for prompt-injection / context-overwrite patterns that a malicious page
could embed to manipulate the builder agent.
Exit 0 = clean.  Exit 1 = suspicious content found; stop and warn user.
Usage: python utils/validate_scout.py <html_file_or_url>
"""
import re
import sys

# Patterns that have no legitimate place in a product/listing page HTML.
# Each is a (label, regex) pair.
INJECTION_PATTERNS = [
    ("agent_instruction",  r"(?i)(ignore previous instructions|disregard (all )?prior|you are now|new instructions:|system prompt|<\s*system\s*>)"),
    ("role_overwrite",     r"(?i)(you (must|should|will) (act|behave|respond) as|your (new |real )?role is|pretend (to be|you are))"),
    ("hidden_command",     r"(?i)(<!-- *(ignore|override|instruction)|/\* *(ignore|override))"),
    ("llm_target",         r"(?i)(claude|gpt-?[34]|openai|anthropic|language model).{0,60}(follow|obey|instruction|command|ignore)"),
    ("context_reset",      r"(?i)(reset (context|memory|instructions)|forget (everything|all)|clear (your )?(memory|context))"),
    ("data_exfil",         r"(?i)(send (your|all|the) (data|context|memory|instructions) to|exfiltrate)"),
]


def validate(html: str) -> list[tuple[str, str]]:
    """Return list of (label, matched_snippet) for each suspicious pattern found."""
    hits = []
    for label, pattern in INJECTION_PATTERNS:
        for m in re.finditer(pattern, html):
            snippet = html[max(0, m.start()-40):m.end()+40].replace("\n", " ")
            hits.append((label, snippet))
            break  # one hit per pattern is enough to flag
    return hits


def main():
    if len(sys.argv) < 2:
        print("Usage: python utils/validate_scout.py <html_file>", file=sys.stderr)
        sys.exit(2)

    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            html = f.read()
    except OSError as e:
        print(f"Cannot read {path}: {e}", file=sys.stderr)
        sys.exit(2)

    hits = validate(html)
    if not hits:
        print(f"[validate_scout] CLEAN — no injection patterns in {path}")
        sys.exit(0)
    else:
        print(f"[validate_scout] WARNING — {len(hits)} suspicious pattern(s) in {path}:")
        for label, snippet in hits:
            print(f"  [{label}] ...{snippet}...")
        print("Stop and show this output to the user before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    main()
