"""Normalize and filter LLM conflict output."""

from __future__ import annotations

import re
import unicodedata

from pathlight.shared.utils import debug_log
from .schemas import LearningConflict

CONFLICT_TYPES: frozenset[str] = frozenset(
    {
        "modality_access",
        "cognitive_load",
        "behavioral_regulation_stamina",
        "response_demand",
        "participation_structure",
        "task_independence",
    }
)

SEVERITY_VALUES: frozenset[str] = frozenset({"low", "medium", "high"})


def _norm_match_text(s: str) -> str:
    """Unicode + whitespace normalization for substring checks."""
    t = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", " ", t).strip()


def _longest_contiguous_in_haystack(needle: str, haystack: str) -> int:
    """Length of longest needle[i:j] that appears in haystack (case-sensitive, then casefold)."""
    best = 0
    n = len(needle)
    h_cf = haystack.casefold()
    for i in range(n):
        for j in range(n, i, -1):
            if j - i <= best:
                break
            sub = needle[i:j]
            if sub in haystack:
                best = j - i
                break
            sub_cf = sub.casefold()
            if sub_cf in h_cf:
                best = j - i
                break
    return best


def _iep_anchor_accepted(anchor: str, corpus: str) -> bool:
    """True if anchor is plausibly from corpus (exact, normalized, or long contiguous overlap)."""
    if not anchor.strip():
        return False
    if anchor in corpus:
        return True

    na, nc = _norm_match_text(anchor), _norm_match_text(corpus)
    if not na:
        return False
    if na in nc or na.casefold() in nc.casefold():
        return True

    # Models often swap "She has …" in source with "Jasmine has …" in quotes.
    v_she = re.sub(r"^jasmine has\b", "She has", na, flags=re.IGNORECASE)
    v_jas = re.sub(r"^she has\b", "Jasmine has", na, flags=re.IGNORECASE)
    for v in (v_she, v_jas):
        if v != na and (v in nc or v.casefold() in nc.casefold()):
            return True

    L = len(na)
    min_run = max(20, int(0.52 * L)) if L >= 35 else max(12, int(0.85 * L))
    longest = _longest_contiguous_in_haystack(na, nc)
    for v in (v_she, v_jas):
        if v != na:
            longest = max(longest, _longest_contiguous_in_haystack(v, nc))
    return longest >= min_run


def _normalize_severity(raw: str) -> str:
    s = raw.strip().lower()
    if s in SEVERITY_VALUES:
        return s
    debug_log("DEBUG CONFLICT SANITIZE: unknown severity, using medium:", raw)
    return "medium"


def sanitize_learning_conflicts(
    conflicts: list[LearningConflict],
    *,
    barrier_text: str,
) -> list[LearningConflict]:
    """Drop rows with unknown conflict_type or iep_anchor not found in barrier corpus."""

    out: list[LearningConflict] = []
    corpus = barrier_text

    for c in conflicts:
        ctype = c.conflict_type.strip()
        if ctype not in CONFLICT_TYPES:
            debug_log("DEBUG CONFLICT SANITIZE: dropped unknown conflict_type:", ctype)
            continue

        anchor = c.iep_anchor.strip()
        if not anchor:
            debug_log("DEBUG CONFLICT SANITIZE: dropped empty iep_anchor")
            continue
        if not _iep_anchor_accepted(anchor, corpus):
            debug_log(
                "DEBUG CONFLICT SANITIZE: dropped iep_anchor not in barriers:",
                anchor[:120] + ("…" if len(anchor) > 120 else ""),
            )
            continue

        sev = _normalize_severity(c.severity)
        out.append(
            LearningConflict(
                phase_id=c.phase_id.strip(),
                conflict_type=ctype,
                evidence=c.evidence.strip(),
                severity=sev,
                iep_anchor=anchor,
            )
        )

    return out
