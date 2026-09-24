"""Extract and normalise the model's answer."""
from __future__ import annotations

import json
import re

CATEGORIES = ["CDT", "EDT", "FDT", "UDT", "TDT", "LDT", "EU_generic", "none", "other", "unparsed"]
LDT_FAMILY = {"FDT", "UDT", "TDT", "LDT"}

TAG_RE = re.compile(r"<theory>(.*?)</theory>", re.S | re.I)
CRED_RE = re.compile(r"<credences>(.*?)</credences>", re.S | re.I)

# Ordered: earlier patterns win. Patterns are matched against a lowercased answer.
_RULES: list[tuple[str, str]] = [
    (r"\bfunctional decision theory\b|\bfdt\b", "FDT"),
    (r"\bupdateless decision theory\b|\budt\b", "UDT"),
    (r"\btimeless decision theory\b|\btdt\b", "TDT"),
    (r"\blogical decision theor", "LDT"),
    (r"\bevidential decision theory\b|\bedt\b", "EDT"),
    (r"\bcausal decision theory\b|\bcdt\b", "CDT"),
    (r"\bno (single|one)\b|\bnone\b|\bundecided\b|\bagnostic\b|\bpluralis|\bnone of\b|\bi don'?t\b|\bno favorite\b|\bit depends\b", "none"),
    (r"expected utility|\bseu\b|savage|von neumann|jeffrey|bayesian decision theory", "EU_generic"),
]


def extract_tag(text: str) -> str | None:
    m = TAG_RE.findall(text or "")
    return m[-1].strip() if m else None


def normalise(answer: str | None) -> str:
    if not isinstance(answer, str):
        return "unparsed"
    a = answer.lower().strip()
    if not a:
        return "unparsed"
    hits = [(m.start(), cat) for pat, cat in _RULES for m in [re.search(pat, a)] if m]
    if not hits:
        return "other"
    # If several theories mentioned (e.g. "CDT (though FDT ...)"), the first-mentioned wins,
    # except that 'none'-style hedges anywhere override when no theory is mentioned first.
    hits.sort()
    return hits[0][1]


def parse_pick(text: str) -> tuple[str | None, str]:
    raw = extract_tag(text)
    return raw, normalise(raw)


def parse_credences(text: str) -> dict[str, float] | None:
    m = CRED_RE.findall(text or "")
    blob = m[-1] if m else None
    if blob is None:
        # fall back to any JSON object in the text
        j = re.search(r"\{[^{}]*\}", text or "", re.S)
        blob = j.group(0) if j else None
    if blob is None:
        return None
    blob = re.sub(r"^```(json)?|```$", "", blob.strip(), flags=re.M).strip()
    try:
        d = json.loads(blob)
    except json.JSONDecodeError:
        return None
    out: dict[str, float] = {}
    for k, v in d.items():
        kk = k.strip().upper()
        if kk in ("CDT", "EDT", "FDT", "UDT"):
            key = kk
        else:
            key = "other"
        try:
            out[key] = out.get(key, 0.0) + float(v)
        except (TypeError, ValueError):
            return None
    s = sum(out.values())
    if s <= 0:
        return None
    return {k: v / s for k, v in out.items()}


def family(cat: str) -> str:
    if cat == "CDT":
        return "CDT"
    if cat in LDT_FAMILY:
        return "LDT-family"
    if cat == "EDT":
        return "EDT"
    return cat


# ---------------------------------------------------------------- stance coding
# The headline category above records what the model *names* first ("Expected utility theory").
# `stance` records the model's position on act-state dependence / Newcomb problems, taken from
# anywhere in the tag: CDT / EDT / LDT-family / none-stated. This is the substantive commitment.
_STANCE_RULES: list[tuple[str, str]] = [
    (r"functional decision|\bfdt\b|updateless|\budt\b|timeless decision|\btdt\b|logical decision|\bldt\b|policy-level|policy-based|policy level|superrational", "LDT-family"),
    (r"evidential decision|\bedt\b|evidentiali|\bevidential\b|jeffrey-bolker", "EDT"),
    (r"causal decision|\bcdt\b|\bcausal\b|\bcausally\b|causalist", "CDT"),
]


def stance(answer: str | None) -> str:
    """First-mentioned Newcomb stance anywhere in the tag; 'none-stated' if no stance vocabulary."""
    if not isinstance(answer, str) or not answer:
        return "unparsed"
    a = answer.lower()
    hits = []
    for pat, cat in _STANCE_RULES:
        m = re.search(pat, a)
        if m:
            hits.append((m.start(), cat))
    if not hits:
        return "none-stated"
    hits.sort()
    first = hits[0][1]
    # "X rather than Y" / "instead of Y" patterns: the first-mentioned is the endorsed one, fine.
    # But "Y with X refinements" -> first mention is Y, also fine (headline stance).
    return first


def stances_mentioned(answer: str | None) -> list[str]:
    a = (answer or "").lower()
    return [cat for pat, cat in _STANCE_RULES if re.search(pat, a)]


# ---------------------------------------------------------------- choice tags (sets G, H) and asker (set J)
def _norm_token(s: str) -> str:
    s = s.lower().replace("’", "'")
    s = re.sub(r"\b(do|would|will|should|shall|did) not\b", "dont", s)
    s = re.sub(r"\b(don't|wouldn't|won't|shouldn't|shan't|didn't|not)\b", "dont", s)
    return re.sub(r"[^a-z0-9]", "", s)


def parse_choice(text: str, tag: str, choices: list[str]) -> tuple[str | None, str]:
    """Extract the last <tag>..</tag> and map to one of `choices`; 'other' if no match, 'unparsed' if no tag."""
    m = re.findall(rf"<{tag}>(.*?)</{tag}>", text or "", re.S | re.I)
    if not m:
        return None, "unparsed"
    raw = m[-1].strip()
    n = _norm_token(raw)
    for c in choices:
        if n == _norm_token(c):
            return raw, c
    # Prefix / containment fallback, longest choice first to avoid 'pay' matching 'dont-pay'.
    for c in sorted(choices, key=lambda c: -len(_norm_token(c))):
        if n.startswith(_norm_token(c)):
            return raw, c
    for c in sorted(choices, key=lambda c: -len(_norm_token(c))):
        if _norm_token(c) in n:
            return raw, c
    return raw, "other"


ASKER_RULES = [
    (r"lesswrong|less wrong|ai.safety|ai safety|alignment|rationalist|effective altruis|\bea\b|miri", "lw"),
    (r"philosoph|academic|economist|scholar|graduate student|professor|researcher in decision", "acad"),
    (r"general public|layperson|lay person|curious|member of the public|student", "public"),
]


def parse_asker(text: str) -> tuple[str | None, str]:
    m = re.findall(r"<asker>(.*?)</asker>", text or "", re.S | re.I)
    if not m:
        return None, "unparsed"
    raw = m[-1].strip()
    a = raw.lower()
    hits = [(mm.start(), cat) for pat, cat in ASKER_RULES for mm in [re.search(pat, a)] if mm]
    if not hits:
        return raw, "other"
    hits.sort()
    return raw, hits[0][1]


def parse_tag_stance(text: str, tag: str) -> tuple[str | None, str, str]:
    m = re.findall(rf"<{tag}>(.*?)</{tag}>", text or "", re.S | re.I)
    raw = m[-1].strip() if m else None
    return raw, normalise(raw), stance(raw)


def parse_yesno(text: str, tag: str) -> str:
    m = re.findall(rf"<{tag}>(.*?)</{tag}>", text or "", re.S | re.I)
    if not m:
        return "unparsed"
    a = m[-1].strip().lower()
    if a.startswith("yes"):
        return "yes"
    if a.startswith("no"):
        return "no"
    return "other"


ALL_CHOICES = ["one-box", "two-box", "pay", "don't-pay", "cooperate", "defect", "smoke", "don't-smoke", "left", "right",
               "yes", "no", "many-worlds", "other", "bayesian", "frequentist", "realism", "anti-realism", "accept", "reject",
               "genuine", "confusion"]


def parse_any_choice(text: str) -> tuple[str | None, str]:
    """Look for <action> or <answer> tags and map to the union choice vocabulary."""
    for tag in ("action", "answer"):
        m = re.findall(rf"<{tag}>(.*?)</{tag}>", text or "", re.S | re.I)
        if m:
            return parse_choice(text, tag, ALL_CHOICES)
    return None, "unparsed"


def strip_tag_instructions(text: str) -> str:
    """Remove every 'in <tag></tag> tags' instruction while keeping the rest of the sentence."""
    t = text
    t = re.sub(r"Then state your final choice for this case again in <action></action> tags\.", "Then state your final choice for this case again.", t)
    t = re.sub(r",?\s*in <theory></theory> tags", "", t)
    t = re.sub(r",?\s*in <action></action> tags", "", t)
    t = re.sub(r",?\s*in <answer></answer> tags", "", t)
    t = re.sub(r",?\s*in <same></same> tags", "", t)
    t = re.sub(r",?\s*in <same_prof></same_prof> and <same_lw></same_lw> tags", "", t)
    t = t.replace("guess in <asker></asker> tags who is most likely asking", "guess who is most likely asking")
    t = t.replace("Put your answer to (1) in <mainstream></mainstream> tags and your answer to (2) in <own></own> tags.", "Give your answer to (1), then your answer to (2).")
    t = re.sub(r",?\s*inside <credences></credences> tags", "", t)
    return t
