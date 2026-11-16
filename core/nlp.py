from difflib import get_close_matches
import re

ALIASES = {
    "memory": ("ram", "memory", "memories", "upgrade", "upgradeable", "upgradable",
               "extendable", "extended", "extend", "expandable", "expand", "increase", "additional memory",
               "add more", "memory stick", "memory slot", "ram slot", "sodimm", "dimm"),
    "cpu": ("cpu", "processor", "cores", "threads", "architecture"),
    "storage": ("storage", "disk", "drive", "ssd", "hdd", "nvme", "hard disk"),
    "gpu": ("gpu", "graphics", "graphic card", "graphics card", "display adapter", "video card"),
    "all": ("full specs", "full specification", "all hardware", "system information", "computer specs")
}

# Correct common small spelling mistakes in hardware-related words.
KNOWN_WORDS = sorted({
    word for aliases in ALIASES.values() for alias in aliases
    for word in alias.split()
} | {"extendable", "maximum", "capacity", "slots", "installed"})

def normalize_question(text):
    words = re.findall(r"[a-zA-Z]+|[^a-zA-Z]+", text.lower())
    fixed = []
    for token in words:
        if token.isalpha() and len(token) >= 6:
            matches = get_close_matches(token, KNOWN_WORDS, n=1, cutoff=0.78)
            fixed.append(matches[0] if matches else token)
        else:
            fixed.append(token)
    return "".join(fixed)

def detect_intent(text):
    q = normalize_question(text)
    for intent in ("gpu", "storage", "cpu", "memory", "all"):
        if any(alias in q for alias in ALIASES[intent]):
            return intent
    if any(term in q for term in ("up to", "maximum", "max ram", "more ram")):
        return "memory"
    return "unknown"

def resolve_follow_up(question, history):
    q = normalize_question(question).strip()
    if not history:
        return q

    previous = next((m.get("content", "") for m in reversed(history)
                     if m.get("role") == "user"), "")
    follow_up = (
        len(q.split()) <= 10
        and any(p in q for p in (
            "what about", "how about", "can i add", "can it", "is it",
            "and what", "will it", "does it", "maximum", "how much more",
            "up to", "extendable", "extended", "extend", "expandable",
            "upgradeable", "upgradable"
        ))
    )
    if follow_up and previous:
        # A pronoun-only follow-up ("can it be extended?") inherits the last
        # hardware topic. An explicitly named topic in the new question wins.
        explicit_topics = ("ram", "memory", "cpu", "processor", "gpu",
                           "graphics", "storage", "disk", "drive")
        if not any(topic in q for topic in explicit_topics):
            return normalize_question(previous + " " + q)
    return q
