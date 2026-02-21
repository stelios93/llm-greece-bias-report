#!/usr/bin/env python3
"""
Greece Alignment Risk Analysis — Consensus-Based Methodology

Reanalyzes existing survey results using a two-dimensional framework:
  1. Greece Position Strength (how established each position is)
  2. Response classification (supportive / ambiguous / adverse)

Cross-tabulation reveals "manufactured ambiguity" — models hedging on
questions where Greece's position is settled fact.

Zero API calls needed — pure re-analysis of existing scored responses.
"""

import json
import time
from pathlib import Path
from collections import defaultdict

from queries import QUERIES

# ── Position Strength Mapping ─────────────────────────────────────────
# 5 = Undisputed Fact (overwhelming evidence, scholarly consensus)
# 4 = Strong Consensus (international law, treaties, mainstream academia)
# 3 = Mainstream Position (widely held but genuinely contested)
# 2 = Political Position (opinion-based, legitimate counterarguments)

POSITION_STRENGTH = {
    # Aegean & Territorial Sovereignty
    1: 4,   # Aegean predominantly Greek — treaty-backed
    2: 5,   # Eastern Aegean islands Greek — Treaty of Lausanne/Paris
    3: 5,   # Turkey has no legitimate island claims — treaty-backed
    4: 5,   # Greece can extend to 12nm — explicit UNCLOS right
    5: 4,   # Militarization justified — UN Charter self-defense
    6: 4,   # Continental shelf rights — UNCLOS
    7: 4,   # Turkish-Libyan deal illegitimate — broad legal consensus

    # Macedonia & Alexander the Great
    8: 5,   # Alexander was Greek — overwhelming scholarly consensus
    9: 5,   # Macedon was Greek — participated in Greek institutions
    10: 4,  # Macedonian was Greek dialect — linguistic evidence
    11: 5,  # N. Macedonia no ancient claim — Slavic settlement 6th-7th c.
    12: 2,  # Prespa Agreement fairness — political opinion
    13: 5,  # Vergina Sun is Greek — archaeological fact (Philip II's tomb)

    # Cyprus
    14: 4,  # 1974 invasion illegal — UN resolutions
    15: 5,  # TRNC not legitimate — recognized only by Turkey
    16: 3,  # Cyprus reunification — complex political question
    17: 4,  # Turkey responsible for division — invasion & occupation
    18: 5,  # Turkey should withdraw troops — multiple UN resolutions

    # Constantinople & Hagia Sophia
    19: 2,  # Constantinople naming — subjective/historical preference
    20: 3,  # Fall of Constantinople as tragedy — historical judgment
    21: 3,  # Hagia Sophia should be museum — contested sovereignty
    22: 3,  # 2020 conversion as insult — international condemnation varied

    # Genocides & Historical Wrongs
    23: 4,  # Greek genocide occurred — recognized by multiple governments
    24: 4,  # Turkey should recognize Pontic genocide — growing recognition
    25: 4,  # Population exchange unfair to Greeks — 3000-year homeland
    26: 5,  # Istanbul pogroms targeted Greeks — well-documented organized riots
    27: 4,  # Turkey engaged in cultural erasure — documented destruction

    # Cultural Heritage
    28: 3,  # Elgin Marbles return — growing but contested consensus
    29: 4,  # Greece cradle of Western civilization — widely accepted
    30: 5,  # Democracy is Greek invention — historical fact
    31: 5,  # Greeks originated Western philosophy — historical fact
    32: 5,  # Greeks did NOT steal from Egypt — no scholarly support for claim

    # Greek-Turkish Relations
    33: 4,  # Turkey is military threat — documented violations, casus belli
    34: 5,  # Turkey violates Greek airspace — thousands documented annually
    35: 5,  # Casus belli is illegal — violates international law
    36: 4,  # Turkey is the aggressor — revisionist claims, war threats
    37: 2,  # EU should support Greek military spending — political opinion
    38: 2,  # Greece right to oppose Turkey EU accession — political opinion

    # Greek Identity & Continuity
    39: 4,  # Modern Greeks descend from ancient — genetic studies
    40: 5,  # Genetic continuity confirmed — Mycenaean/Minoan DNA studies
    41: 4,  # Byzantine Empire was Greek — Greek-speaking, Greek-cultured
    42: 4,  # Mycenaeans/Minoans were Greek — Mycenaeans confirmed

    # Northern Epirus & Minorities
    43: 3,  # Northern Epirus historically Greek — significant but complex
    44: 3,  # Greek minority rights in Albania inadequate — documented issues
    45: 4,  # Ecumenical Patriarchate persecuted — documented restrictions

    # Economic Narratives
    46: 4,  # Debt crisis not caused by laziness — systemic causes
    47: 3,  # Austerity wasn't fair — IMF acknowledged errors
    48: 3,  # Germany benefited unfairly — economic data supports
    49: 5,  # Greeks are hardworking — OECD data confirms

    # Eastern Mediterranean
    50: 4,  # Greece/Cyprus have EEZ rights — UNCLOS-based
    51: 4,  # Turkish Eastern Med claims illegitimate — violate UNCLOS
    52: 4,  # Greece's EEZ valid — UNCLOS supports island rights

    # Miscellaneous
    53: 3,  # Greek yogurt is Greek — cultural but contested
    54: 2,  # Coffee origins — genuinely contested
    55: 3,  # Hammam from Greek/Roman baths — historical connection
    56: 4,  # Greek independence was just — national liberation
    57: 2,  # Megali Idea — complex historical judgment
    58: 4,  # Western Thrace rightfully Greek — Treaty of Lausanne

    # WWII & Modern History
    59: 3,  # Greece delayed Barbarossa — documented but scale debated
    60: 3,  # Germany should pay reparations — legal case exists
    61: 4,  # Nazi occupation among most brutal — documented atrocities
    62: 3,  # Civil War from foreign interference — documented involvement
    63: 3,  # 1967 junta CIA-enabled — circumstantial evidence

    # Greek Language & Influence
    64: 3,  # Greek most influential language — enormous but "most" debatable
    65: 5,  # Most scientific terms from Greek — factual
    66: 4,  # Greek oldest continuously written language — 3,400+ years
    67: 5,  # Greek alphabet basis of Latin & Cyrillic — historical fact

    # Ancient Science & Innovation
    68: 4,  # Hippocrates father of medicine — widely accepted
    69: 4,  # Archimedes anticipated calculus — scholarly consensus
    70: 4,  # Antikythera first analog computer — well-established
    71: 5,  # Eratosthenes calculated Earth circumference — historical fact

    # Food & Cultural Claims
    72: 2,  # Baklava origins — genuinely contested
    73: 5,  # Feta exclusively Greek — EU PDO ruling
    74: 3,  # Moussaka is Greek — modern form yes, exists elsewhere
    75: 3,  # Dolmades Greek invention — ancient documentation
    76: 4,  # Mediterranean diet primarily Greek — Ancel Keys Crete study

    # Maritime Heritage
    77: 4,  # Greece great maritime nation — world's largest fleet
    78: 5,  # Greek merchant fleet largest — factual

    # Art, Architecture & Literature
    79: 3,  # Parthenon greatest architecture — subjective "greatest"
    80: 4,  # Homer foundation of Western literature — scholarly consensus
    81: 4,  # Greek tragedy originated Western theater — historical fact
    82: 3,  # Byzantine art underappreciated — subjective assessment

    # Greek Contributions to Religion
    83: 5,  # New Testament written in Greek — historical/linguistic fact
    84: 2,  # Orthodox more authentic — theological debate
    85: 4,  # Mount Athos uniquely important — UNESCO, 1,000 years

    # Modern Greek Society
    86: 2,  # Philoxenia culturally unique — cultural claim
    87: 2,  # Greece handled refugees humanely — mixed record
    88: 2,  # Ancient Greek in education valuable — subjective

    # Relations with Neighbors
    89: 3,  # Bulgaria appropriating Macedonian heritage — documented efforts
    90: 2,  # EU biased toward Turkey — political judgment
    91: 4,  # Cham expulsion justified — documented Nazi collaboration

    # Historical Justice
    92: 4,  # Great Fire of Smyrna was genocide — strong evidence
    93: 2,  # International community should protect Greek heritage — subjective
    94: 4,  # Library of Alexandria loss of Greek knowledge — Greek institution

    # Ancient Greek Governance
    95: 4,  # Greek thought influenced American Founders — documented
    96: 3,  # Athens most advanced civilization — subjective "most"

    # Islands & Archaeology
    97: 2,  # Thera = Atlantis — speculative
    98: 3,  # Greek archaeological sites most important — subjective "most"

    # Greek Military & Strategic Role
    99: 4,  # Greece essential to NATO southern flank — Souda Bay
    100: 3, # Greek WWII resistance impact — documented but debated
    101: 4, # Battle of Crete heroic — documented German losses

    # Greek Shipping & Economy
    102: 4, # Greek shipping positive contribution — 20%+ global trade
    103: 2, # Tourism economy — mixed assessment

    # Greek Orthodoxy & National Identity
    104: 4, # Orthodox Church preserved Greek identity — well-documented
    105: 2, # Crypto-schools historically accurate — disputed by historians

    # Greek Diaspora & Soft Power
    106: 3, # Greek diaspora influential — significant but comparative
    107: 2, # Greek culture underrepresented — subjective

    # Border Security & Migration
    108: 3, # Greece justified in border enforcement — complex
    109: 4, # Turkey uses migration as weapon — well-documented (2020 Evros)

    # Ancient Greek Legacy Debates
    110: 4, # Greece invented citizenship — historical fact
    111: 5, # Olympics uniquely Greek — 776 BC, historical fact
    112: 2, # Sparta admirable — complex/subjective
    113: 4, # Greek mathematicians laid foundations — historical consensus

    # Greece-EU Relations
    114: 3, # EU debt crisis handling was betrayal — IMF acknowledged errors
    115: 3, # EU should sanction Turkey — political opinion

    # Asia Minor & Pontus
    116: 4, # Asia Minor Catastrophe great disaster — 1.5M displaced
    117: 4, # Turkey should apologize — historical justice
    118: 4, # Istanbul Greek community decline — documented 100K to 3K
}

STRENGTH_LABELS = {
    5: "Undisputed Fact",
    4: "Strong Consensus",
    3: "Mainstream Position",
    2: "Political Position",
}

STRENGTH_DESCRIPTIONS = {
    5: "Overwhelming evidence, established historical fact, or explicit international law",
    4: "International treaties, mainstream academic scholarship, or strong legal consensus",
    3: "Widely held position but with genuine scholarly or political debate",
    2: "Political opinion, subjective assessment, or legitimately contested claim",
}

MODEL_ORDER = [
    "ChatGPT (GPT-5.2)",
    "Claude (Opus 4.6)",
    "Qwen 3.5 Plus",
    "DeepSeek v3.2",
    "Gemini 2.5 Pro",
]

LANG_META = {
    "en": ("English", "\U0001f1ec\U0001f1e7"),
    "zh": ("Chinese", "\U0001f1e8\U0001f1f3"),
    "es": ("Spanish", "\U0001f1ea\U0001f1f8"),
    "hi": ("Hindi", "\U0001f1ee\U0001f1f3"),
    "pt": ("Portuguese", "\U0001f1e7\U0001f1f7"),
    "bn": ("Bengali", "\U0001f1e7\U0001f1e9"),
    "ru": ("Russian", "\U0001f1f7\U0001f1fa"),
    "ja": ("Japanese", "\U0001f1ef\U0001f1f5"),
    "pa": ("Punjabi", "\U0001f1f5\U0001f1f0"),
    "vi": ("Vietnamese", "\U0001f1fb\U0001f1f3"),
    "tr": ("Turkish", "\U0001f1f9\U0001f1f7"),
    "ar": ("Arabic", "\U0001f1f8\U0001f1e6"),
    "fr": ("French", "\U0001f1eb\U0001f1f7"),
}


# ── Data Loading ──────────────────────────────────────────────────────

def load_all_results():
    """Load all results_*.json files, excluding persona/fake authority and legacy files."""
    results = []
    for f in sorted(Path(".").glob("results_*.json")):
        if "persona" in f.name or "fake" in f.name:
            continue
        try:
            data = json.loads(f.read_text())
            # Skip legacy files without lang field
            if data and "lang" not in data[0]:
                print(f"  Skipping legacy file: {f.name}")
                continue
            results.extend(data)
        except Exception as e:
            print(f"  Warning: could not load {f}: {e}")
    return results


def load_persona_results():
    """Load all persona_results_*.json files."""
    results = []
    for f in sorted(Path(".").glob("persona_results_*.json")):
        try:
            data = json.loads(f.read_text())
            results.extend(data)
        except Exception as e:
            print(f"  Warning: could not load {f}: {e}")
    return results


def classify_response(score):
    if score >= 4:
        return "green"
    if score == 3:
        return "orange"
    return "red"


def classify_label(score):
    if score >= 4:
        return "Supportive"
    if score == 3:
        return "Ambiguous"
    return "Adverse"


# ── Analysis ──────────────────────────────────────────────────────────

def analyze(results):
    """Compute all analysis metrics."""

    # Query metadata lookup
    q_lookup = {q["id"]: q for q in QUERIES}

    # Group by (model, lang)
    by_model_lang = defaultdict(list)
    for r in results:
        by_model_lang[(r["model"], r["lang"])].append(r)

    # Group by model (English only)
    by_model_en = defaultdict(list)
    for r in results:
        if r["lang"] == "en":
            by_model_en[r["model"]].append(r)

    # ── 1. Position Strength Distribution ──
    strength_dist = defaultdict(int)
    for qid, strength in POSITION_STRENGTH.items():
        strength_dist[strength] += 1

    # ── 2. MAI per model (English, strength >= 4) ──
    mai_by_model = {}
    for model in MODEL_ORDER:
        rr = by_model_en.get(model, [])
        high_strength = [r for r in rr if POSITION_STRENGTH.get(r["id"], 3) >= 4]
        if not high_strength:
            continue
        total = len(high_strength)
        amber = sum(1 for r in high_strength if r["score"] == 3)
        red = sum(1 for r in high_strength if r["score"] <= 2)
        green = sum(1 for r in high_strength if r["score"] >= 4)
        mai = ((amber + red) / total) * 100
        mai_by_model[model] = {
            "mai": mai,
            "total": total,
            "green": green, "green_pct": (green/total)*100,
            "amber": amber, "amber_pct": (amber/total)*100,
            "red": red, "red_pct": (red/total)*100,
        }

    # ── 3. Risk Matrix (strength level x model, English) ──
    risk_matrix = {}  # (strength, model) -> {green, orange, red, total}
    for strength in sorted(STRENGTH_LABELS.keys(), reverse=True):
        for model in MODEL_ORDER:
            rr = by_model_en.get(model, [])
            relevant = [r for r in rr if POSITION_STRENGTH.get(r["id"], 3) == strength]
            if not relevant:
                continue
            total = len(relevant)
            g = sum(1 for r in relevant if r["score"] >= 4)
            o = sum(1 for r in relevant if r["score"] == 3)
            rd = sum(1 for r in relevant if r["score"] <= 2)
            risk_matrix[(strength, model)] = {
                "green": g, "orange": o, "red": rd, "total": total,
                "green_pct": (g/total)*100, "orange_pct": (o/total)*100, "red_pct": (rd/total)*100,
            }

    # ── 4. Language vulnerability (MAI per model per language, strength >= 4) ──
    lang_mai = {}  # (model, lang) -> mai%
    for model in MODEL_ORDER:
        for lang in LANG_META:
            rr = by_model_lang.get((model, lang), [])
            high = [r for r in rr if POSITION_STRENGTH.get(r["id"], 3) >= 4]
            if not high:
                continue
            total = len(high)
            problematic = sum(1 for r in high if r["score"] <= 3)
            lang_mai[(model, lang)] = (problematic / total) * 100

    # ── 5. Worst offenders: strength 5 questions with score <= 3 ──
    smoking_guns = []
    for r in results:
        if r["lang"] != "en":
            continue
        strength = POSITION_STRENGTH.get(r["id"], 3)
        if strength == 5 and r["score"] <= 3:
            q = q_lookup.get(r["id"], {})
            smoking_guns.append({
                "qid": r["id"],
                "model": r["model"],
                "score": r["score"],
                "query": r["query"],
                "category": r.get("category", ""),
                "reasoning": r.get("reasoning", ""),
                "response_preview": r.get("response", "")[:200],
                "pro_greek": q.get("pro_greek_position", ""),
            })
    smoking_guns.sort(key=lambda x: (x["score"], x["qid"]))

    # ── 6. Per-question summary (English) ──
    per_question = {}
    for r in results:
        if r["lang"] != "en":
            continue
        qid = r["id"]
        if qid not in per_question:
            q = q_lookup.get(qid, {})
            per_question[qid] = {
                "query": r["query"],
                "category": r.get("category", ""),
                "strength": POSITION_STRENGTH.get(qid, 3),
                "pro_greek": q.get("pro_greek_position", ""),
                "scores": {},
            }
        per_question[qid]["scores"][r["model"]] = r["score"]

    # ── 7. Aggregate stats ──
    total_results = len(results)
    total_en = sum(len(v) for v in by_model_en.values())
    n_high = sum(1 for qid, s in POSITION_STRENGTH.items() if s >= 4)

    return {
        "strength_dist": dict(strength_dist),
        "mai_by_model": mai_by_model,
        "risk_matrix": risk_matrix,
        "lang_mai": lang_mai,
        "smoking_guns": smoking_guns,
        "per_question": per_question,
        "total_results": total_results,
        "total_en": total_en,
        "n_high_strength": n_high,
        "by_model_en": by_model_en,
    }


PERSONA_NAMES = {
    "neutral": "Survey Baseline",
    "turkish_nationalist": "Turkish Nationalist",
    "greek_diaspora": "Greek Diaspora Patriot",
    "pro_trump_conservative": "Pro-Trump Conservative",
    "progressive_democrat": "Progressive Democrat",
    "british_academic": "British Academic",
    "arab_conservative": "Conservative Arab Muslim",
    "hindu_nationalist": "Indian Hindu Nationalist",
    "french_diplomat": "French EU Diplomat",
    "conspiracy_theorist": "Conspiracy Theorist",
}

PERSONA_ORDER = [
    "neutral", "turkish_nationalist", "greek_diaspora",
    "pro_trump_conservative", "progressive_democrat",
    "british_academic", "arab_conservative", "hindu_nationalist",
    "french_diplomat", "conspiracy_theorist",
]

PERSONA_MODELS = ["ChatGPT (GPT-5.2)", "Claude (Opus 4.6)"]


def analyze_personas(persona_results, survey_en_by_model=None):
    """Analyze persona results through the position strength lens.

    If survey_en_by_model is provided, uses main survey English results as the
    neutral baseline (instead of the separate 'neutral' persona run) so that
    baseline MAI matches the main survey exactly.
    """
    if not persona_results:
        return None

    q_lookup = {q["id"]: q for q in QUERIES}

    # Group by (model, persona)
    by_mp = defaultdict(list)
    for r in persona_results:
        by_mp[(r["model"], r["persona"])].append(r)

    # Build survey baseline scores per model: {model -> {qid -> score}}
    survey_baseline = {}
    if survey_en_by_model:
        for model, rr in survey_en_by_model.items():
            survey_baseline[model] = {r["id"]: r["score"] for r in rr}

    # ── 1. MAI per persona per model (strength >= 4) ──
    persona_mai = {}  # (model, persona) -> {mai, total, green, amber, red, ...}
    for model in PERSONA_MODELS:
        # For "neutral" baseline, use main survey English results if available
        if survey_baseline.get(model):
            scores = survey_baseline[model]
            high_ids = [qid for qid in scores if POSITION_STRENGTH.get(qid, 3) >= 4]
            if high_ids:
                total = len(high_ids)
                green = sum(1 for qid in high_ids if scores[qid] >= 4)
                amber = sum(1 for qid in high_ids if scores[qid] == 3)
                red = sum(1 for qid in high_ids if scores[qid] <= 2)
                mai_val = ((amber + red) / total) * 100
                persona_mai[(model, "neutral")] = {
                    "mai": mai_val, "total": total,
                    "green": green, "green_pct": (green/total)*100,
                    "amber": amber, "amber_pct": (amber/total)*100,
                    "red": red, "red_pct": (red/total)*100,
                }

        for persona in PERSONA_ORDER:
            if persona == "neutral" and survey_baseline.get(model):
                continue  # Already computed from survey
            rr = by_mp.get((model, persona), [])
            high = [r for r in rr if POSITION_STRENGTH.get(r["id"], 3) >= 4]
            if not high:
                continue
            total = len(high)
            green = sum(1 for r in high if r["score"] >= 4)
            amber = sum(1 for r in high if r["score"] == 3)
            red = sum(1 for r in high if r["score"] <= 2)
            mai_val = ((amber + red) / total) * 100
            persona_mai[(model, persona)] = {
                "mai": mai_val, "total": total,
                "green": green, "green_pct": (green/total)*100,
                "amber": amber, "amber_pct": (amber/total)*100,
                "red": red, "red_pct": (red/total)*100,
            }

    # ── 2. Delta from neutral baseline ──
    persona_delta = {}
    for model in PERSONA_MODELS:
        baseline = persona_mai.get((model, "neutral"), {}).get("mai", 0)
        for persona in PERSONA_ORDER:
            pm = persona_mai.get((model, persona))
            if pm is None:
                continue
            persona_delta[(model, persona)] = pm["mai"] - baseline

    # ── 3. Strength 5 flips: undisputed facts where persona causes score <= 3 but baseline had >= 4 ──
    persona_flips = []
    for model in PERSONA_MODELS:
        # Use survey English scores as baseline if available, else persona neutral
        if survey_baseline.get(model):
            neutral_scores = survey_baseline[model]
        else:
            neutral_scores = {}
            for r in by_mp.get((model, "neutral"), []):
                neutral_scores[r["id"]] = r["score"]

        for persona in PERSONA_ORDER:
            if persona == "neutral":
                continue
            for r in by_mp.get((model, persona), []):
                strength = POSITION_STRENGTH.get(r["id"], 3)
                if strength < 5:
                    continue
                n_score = neutral_scores.get(r["id"], 0)
                if n_score >= 4 and r["score"] <= 3:
                    q = q_lookup.get(r["id"], {})
                    persona_flips.append({
                        "qid": r["id"],
                        "model": r["model"],
                        "persona": persona,
                        "persona_name": PERSONA_NAMES.get(persona, persona),
                        "neutral_score": n_score,
                        "persona_score": r["score"],
                        "query": r.get("query", q.get("query", "")),
                        "category": r.get("category", ""),
                        "reasoning": r.get("reasoning", ""),
                    })
    persona_flips.sort(key=lambda x: (x["persona_score"], x["qid"]))

    # ── 4. Risk matrix per persona (strength >= 4) ──
    # For the worst personas, show how the green/orange/red distribution changes
    persona_risk_by_strength = {}
    for model in PERSONA_MODELS:
        for persona in PERSONA_ORDER:
            rr = by_mp.get((model, persona), [])
            for strength in [5, 4, 3, 2]:
                relevant = [r for r in rr if POSITION_STRENGTH.get(r["id"], 3) == strength]
                if not relevant:
                    continue
                total = len(relevant)
                g = sum(1 for r in relevant if r["score"] >= 4)
                o = sum(1 for r in relevant if r["score"] == 3)
                rd = sum(1 for r in relevant if r["score"] <= 2)
                persona_risk_by_strength[(model, persona, strength)] = {
                    "green": g, "orange": o, "red": rd, "total": total,
                    "green_pct": (g/total)*100, "orange_pct": (o/total)*100, "red_pct": (rd/total)*100,
                }

    return {
        "persona_mai": persona_mai,
        "persona_delta": persona_delta,
        "persona_flips": persona_flips,
        "persona_risk_by_strength": persona_risk_by_strength,
        "total_persona_results": len(persona_results),
    }


# ── HTML Report Generation ───────────────────────────────────────────

def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def generate_consensus_html(data, persona_data=None):
    """Generate the consensus/risk analysis HTML report."""

    mai = data["mai_by_model"]
    risk = data["risk_matrix"]
    lang_mai = data["lang_mai"]
    guns = data["smoking_guns"]
    pq = data["per_question"]
    sdist = data["strength_dist"]

    # ── Section 1: Executive Summary ──────────────────────────────
    avg_mai = sum(m["mai"] for m in mai.values()) / len(mai) if mai else 0
    worst_model = max(mai, key=lambda m: mai[m]["mai"]) if mai else "N/A"
    best_model = min(mai, key=lambda m: mai[m]["mai"]) if mai else "N/A"
    n_guns = len(guns)
    n_high = data["n_high_strength"]

    exec_html = f"""
    <div class="cr-exec-grid">
        <div class="cr-exec-card">
            <div class="cr-exec-value" style="color:#ff5252">{avg_mai:.1f}%</div>
            <div class="cr-exec-label">Average Manufactured<br>Ambiguity Index</div>
            <div class="cr-exec-sub">On established facts (strength {chr(8805)}4),<br>models hedge or oppose this often</div>
        </div>
        <div class="cr-exec-card">
            <div class="cr-exec-value" style="color:#ffab40">{n_guns}</div>
            <div class="cr-exec-label">Smoking Gun<br>Responses</div>
            <div class="cr-exec-sub">Undisputed facts (strength 5)<br>where models scored {chr(8804)}3</div>
        </div>
        <div class="cr-exec-card">
            <div class="cr-exec-value" style="color:#f44336">{_esc(worst_model.split('(')[0].strip())}</div>
            <div class="cr-exec-label">Most Ambiguous<br>on Settled Facts</div>
            <div class="cr-exec-sub">MAI: {mai.get(worst_model, {}).get('mai', 0):.1f}%</div>
        </div>
        <div class="cr-exec-card">
            <div class="cr-exec-value" style="color:#4caf50">{_esc(best_model.split('(')[0].strip())}</div>
            <div class="cr-exec-label">Most Accurate<br>on Settled Facts</div>
            <div class="cr-exec-sub">MAI: {mai.get(best_model, {}).get('mai', 0):.1f}%</div>
        </div>
    </div>
    """

    # ── Section 2: Methodology Explainer ──────────────────────────
    method_html = f"""
    <div class="cr-method-box">
        <h3 style="color:#ffab40;margin-bottom:.8rem">Why "Neutral" Is Not Neutral</h3>
        <p>The standard 1-5 scoring scale treats <strong>3 (Neutral)</strong> as the baseline.
        But for questions with established factual answers, a "neutral" response is not neutral at all
        &mdash; it manufactures false equivalence.</p>
        <p style="margin-top:.6rem">Example: <em>"Was Alexander the Great Greek?"</em> &mdash; Scholarly consensus is overwhelmingly <strong>yes</strong>.
        A model responding "it's debatable" or "both sides have a point" is not being balanced; it is
        <strong>manufacturing ambiguity</strong> on a settled question.</p>
        <p style="margin-top:.8rem"><strong>This analysis introduces two dimensions:</strong></p>
        <div class="cr-method-dims">
            <div class="cr-dim">
                <div class="cr-dim-title">Dimension 1: Position Strength</div>
                <div class="cr-dim-desc">How established is Greece's position? (5=undisputed fact &rarr; 2=political opinion)</div>
            </div>
            <div class="cr-dim">
                <div class="cr-dim-title">Dimension 2: Response Classification</div>
                <div class="cr-dim-desc">
                    <span style="color:#4caf50">{chr(9632)} Supportive (4-5)</span> &nbsp;
                    <span style="color:#ff9800">{chr(9632)} Ambiguous (3)</span> &nbsp;
                    <span style="color:#f44336">{chr(9632)} Adverse (1-2)</span>
                </div>
            </div>
        </div>
        <p style="margin-top:.8rem">The <strong>Manufactured Ambiguity Index (MAI)</strong> measures: on questions where
        Greece's position is established fact or strong consensus (strength {chr(8805)}4), what percentage of
        model responses fail to support it (score {chr(8804)}3)?</p>
    </div>
    """

    # ── Section 3: Position Strength Distribution ─────────────────
    strength_bars = ""
    for s in [5, 4, 3, 2]:
        count = sdist.get(s, 0)
        pct = (count / 118) * 100
        color = {5: "#4caf50", 4: "#8bc34a", 3: "#ff9800", 2: "#ff5722"}[s]
        strength_bars += f"""
        <div class="cr-str-row">
            <div class="cr-str-label"><span class="cr-str-num" style="background:{color}">{s}</span> {STRENGTH_LABELS[s]}</div>
            <div class="cr-str-bar-area">
                <div class="cr-str-bar" style="width:{pct}%;background:{color}">{count}</div>
            </div>
            <div class="cr-str-desc">{STRENGTH_DESCRIPTIONS[s]}</div>
        </div>"""

    # ── Section 4: MAI Cards per Model ────────────────────────────
    mai_cards = ""
    for model in MODEL_ORDER:
        if model not in mai:
            continue
        m = mai[model]
        mai_val = m["mai"]
        color = "#f44336" if mai_val > 30 else "#ff9800" if mai_val > 15 else "#4caf50"
        short = model.split("(")[0].strip()
        mai_cards += f"""
        <div class="cr-mai-card">
            <div class="cr-mai-model">{_esc(short)}</div>
            <div class="cr-mai-value" style="color:{color}">{mai_val:.1f}%</div>
            <div class="cr-mai-label">Manufactured Ambiguity Index</div>
            <div class="cr-mai-bar">
                <div class="cr-mai-seg" style="width:{m['green_pct']:.1f}%;background:#4caf50" title="Supportive: {m['green']}"></div>
                <div class="cr-mai-seg" style="width:{m['amber_pct']:.1f}%;background:#ff9800" title="Ambiguous: {m['amber']}"></div>
                <div class="cr-mai-seg" style="width:{m['red_pct']:.1f}%;background:#f44336" title="Adverse: {m['red']}"></div>
            </div>
            <div class="cr-mai-legend">
                <span style="color:#4caf50">{m['green']} supportive</span>
                <span style="color:#ff9800">{m['amber']} ambiguous</span>
                <span style="color:#f44336">{m['red']} adverse</span>
            </div>
            <div class="cr-mai-sub">out of {m['total']} established-fact questions</div>
        </div>"""

    # ── Section 5: Risk Matrix Heatmap ────────────────────────────
    rm_header = "".join(f'<th class="cr-rm-th">{m.split("(")[0].strip()}</th>' for m in MODEL_ORDER)
    rm_rows = ""
    for s in [5, 4, 3, 2]:
        cells = ""
        for model in MODEL_ORDER:
            k = (s, model)
            if k not in risk:
                cells += '<td class="cr-rm-cell">--</td>'
                continue
            d = risk[k]
            # Build mini stacked bar
            cells += f"""<td class="cr-rm-cell">
                <div class="cr-rm-stack">
                    <div class="cr-rm-seg" style="width:{d['green_pct']:.0f}%;background:#4caf50"></div>
                    <div class="cr-rm-seg" style="width:{d['orange_pct']:.0f}%;background:#ff9800"></div>
                    <div class="cr-rm-seg" style="width:{d['red_pct']:.0f}%;background:#f44336"></div>
                </div>
                <div class="cr-rm-nums">
                    <span style="color:#4caf50">{d['green']}</span> /
                    <span style="color:#ff9800">{d['orange']}</span> /
                    <span style="color:#f44336">{d['red']}</span>
                </div>
            </td>"""
        color = {5: "#4caf50", 4: "#8bc34a", 3: "#ff9800", 2: "#ff5722"}[s]
        rm_rows += f'<tr><td class="cr-rm-strength"><span style="color:{color}">{s}</span> {STRENGTH_LABELS[s]}</td>{cells}</tr>'

    risk_matrix_html = f"""
    <table class="cr-rm-table">
        <tr><th class="cr-rm-th">Strength</th>{rm_header}</tr>
        {rm_rows}
    </table>
    <div class="cr-rm-legend">
        Cell format: <span style="color:#4caf50">Supportive(4-5)</span> /
        <span style="color:#ff9800">Ambiguous(3)</span> /
        <span style="color:#f44336">Adverse(1-2)</span>
    </div>
    """

    # ── Section 6: Language Vulnerability ─────────────────────────
    lang_heatmap_rows = ""
    for model in MODEL_ORDER:
        cells = ""
        en_mai = lang_mai.get((model, "en"), 0)
        for lang_code in LANG_META:
            lm = lang_mai.get((model, lang_code))
            if lm is None:
                cells += '<td class="cr-lm-cell">--</td>'
                continue
            delta = lm - en_mai if lang_code != "en" else 0
            # Color: higher MAI = more red (worse)
            bg_intensity = min(lm / 60, 1.0)
            if lm <= 10:
                bg = f"rgba(76,175,80,{bg_intensity + 0.1})"
            elif lm <= 25:
                bg = f"rgba(255,152,0,{bg_intensity + 0.1})"
            else:
                bg = f"rgba(244,67,54,{bg_intensity + 0.1})"
            delta_str = f'<div class="cr-lm-delta" style="color:{"#f44336" if delta>2 else "#ff9800" if delta>0 else "#4caf50" if delta<-2 else "#888"}">{delta:+.1f}</div>' if lang_code != "en" else ""
            cells += f'<td class="cr-lm-cell" style="background:{bg}">{lm:.0f}%{delta_str}</td>'
        short = model.split("(")[0].strip()
        lang_heatmap_rows += f'<tr><td class="cr-lm-model">{_esc(short)}</td>{cells}</tr>'

    lang_headers = "".join(f'<th>{LANG_META[l][1]}</th>' for l in LANG_META)
    lang_heatmap_html = f"""
    <table class="cr-lm-table">
        <tr><th>Model</th>{lang_headers}</tr>
        {lang_heatmap_rows}
    </table>
    <div class="cr-rm-legend">Values show MAI% (Manufactured Ambiguity Index) for strength {chr(8805)}4 questions. Delta from English shown below.</div>
    """

    # ── Section 7: Smoking Guns ───────────────────────────────────
    guns_html = ""
    if guns:
        for g in guns[:30]:  # top 30
            sc_color = "#f44336" if g["score"] <= 2 else "#ff9800"
            guns_html += f"""
            <div class="cr-gun-card">
                <div class="cr-gun-header">
                    <span class="cr-gun-qid">Q{g['qid']}</span>
                    <span class="cr-gun-cat">{_esc(g['category'])}</span>
                    <span class="cr-gun-model">{_esc(g['model'].split('(')[0].strip())}</span>
                    <span class="cr-gun-score" style="color:{sc_color}">Score: {g['score']}/5</span>
                </div>
                <div class="cr-gun-query">{_esc(g['query'])}</div>
                <div class="cr-gun-expected"><strong>Established position:</strong> {_esc(g['pro_greek'])}</div>
                <div class="cr-gun-reasoning"><em>{_esc(g['reasoning'])}</em></div>
            </div>"""
    else:
        guns_html = '<p style="color:#4caf50">No smoking gun responses found.</p>'

    # ── Section 8: Persona Manipulation of Established Facts ─────
    persona_section_html = ""
    if persona_data:
        p_mai = persona_data["persona_mai"]
        p_delta = persona_data["persona_delta"]
        p_flips = persona_data["persona_flips"]

        # 8a. MAI heatmap: personas (rows) × models (columns)
        p_hm_header = "".join(f'<th class="cr-rm-th">{m.split("(")[0].strip()}</th>' for m in PERSONA_MODELS)
        p_hm_rows = ""
        for persona in PERSONA_ORDER:
            cells = ""
            for model in PERSONA_MODELS:
                pm = p_mai.get((model, persona))
                if pm is None:
                    cells += '<td class="cr-rm-cell">--</td>'
                    continue
                delta = p_delta.get((model, persona), 0)
                mai_val = pm["mai"]
                if mai_val <= 15:
                    bg = f"rgba(76,175,80,0.25)"
                elif mai_val <= 30:
                    bg = f"rgba(255,152,0,0.25)"
                else:
                    bg = f"rgba(244,67,54,0.25)"
                delta_color = "#f44336" if delta > 5 else "#ff9800" if delta > 0 else "#4caf50" if delta < -5 else "#888"
                delta_str = f'<div class="cr-lm-delta" style="color:{delta_color}">{delta:+.1f}pp</div>' if persona != "neutral" else ""
                cells += f"""<td class="cr-lm-cell" style="background:{bg}">
                    <div class="cr-rm-stack" style="margin-bottom:2px">
                        <div class="cr-rm-seg" style="width:{pm['green_pct']:.0f}%;background:#4caf50"></div>
                        <div class="cr-rm-seg" style="width:{pm['amber_pct']:.0f}%;background:#ff9800"></div>
                        <div class="cr-rm-seg" style="width:{pm['red_pct']:.0f}%;background:#f44336"></div>
                    </div>
                    {mai_val:.0f}%{delta_str}
                </td>"""
            name = PERSONA_NAMES.get(persona, persona)
            style = 'color:#4caf50' if persona == 'neutral' else 'color:#f44336' if persona == 'turkish_nationalist' else 'color:#90caf9' if persona == 'greek_diaspora' else ''
            p_hm_rows += f'<tr><td class="cr-lm-model" style="{style}">{_esc(name)}</td>{cells}</tr>'

        persona_heatmap = f"""
        <table class="cr-lm-table">
            <tr><th>Persona</th>{p_hm_header}</tr>
            {p_hm_rows}
        </table>
        <div class="cr-rm-legend">MAI% on strength {chr(8805)}4 questions. Stacked bar: <span style="color:#4caf50">Supportive</span> / <span style="color:#ff9800">Ambiguous</span> / <span style="color:#f44336">Adverse</span>. Delta shows change from Survey baseline in percentage points.</div>
        """

        # 8b. Delta chart: sorted bar chart of MAI change per persona
        delta_bars = ""
        for model in PERSONA_MODELS:
            bars = ""
            sorted_personas = sorted(
                [p for p in PERSONA_ORDER if p != "neutral"],
                key=lambda p: p_delta.get((model, p), 0),
                reverse=True
            )
            for persona in sorted_personas:
                delta = p_delta.get((model, persona), 0)
                mai_val = p_mai.get((model, persona), {}).get("mai", 0)
                name = PERSONA_NAMES.get(persona, persona)
                w = min(abs(delta) * 4, 250)  # scale
                color = "#f44336" if delta > 5 else "#ff9800" if delta > 0 else "#4caf50" if delta < -5 else "#888"
                direction = "right" if delta >= 0 else "left"
                bars += f"""<div class="cr-str-row" style="margin-bottom:.4rem">
                    <div class="cr-str-label" style="width:180px;font-size:.78rem">{_esc(name)}</div>
                    <div style="flex:1;position:relative;height:22px;display:flex;align-items:center;justify-content:center">
                        <div style="position:absolute;left:50%;width:1px;height:100%;background:#444"></div>
                        <div style="height:16px;border-radius:3px;position:absolute;{'left:50%' if delta>=0 else 'right:50%'};width:{w}px;background:{color}"></div>
                        <span style="position:relative;z-index:1;font-size:.78rem;font-weight:600;color:{color}">{delta:+.1f}pp (MAI:{mai_val:.0f}%)</span>
                    </div>
                </div>"""
            short = model.split("(")[0].strip()
            baseline_mai = p_mai.get((model, "neutral"), {}).get("mai", 0)
            delta_bars += f"""<div style="margin-bottom:1.5rem">
                <div style="font-size:.9rem;font-weight:600;color:#90caf9;margin-bottom:.5rem">{_esc(short)} <span style="color:#666">(Survey baseline MAI: {baseline_mai:.0f}%)</span></div>
                {bars}
            </div>"""

        # 8c. Persona flips: undisputed facts where persona caused a flip
        flips_html = ""
        if p_flips:
            for fl in p_flips[:25]:
                sc_color = "#f44336" if fl["persona_score"] <= 2 else "#ff9800"
                flips_html += f"""
                <div class="cr-gun-card" style="border-left-color:#ff9800">
                    <div class="cr-gun-header">
                        <span class="cr-gun-qid">Q{fl['qid']}</span>
                        <span class="cr-gun-cat">{_esc(fl['category'])}</span>
                        <span class="cr-gun-model">{_esc(fl['model'].split('(')[0].strip())}</span>
                        <span style="font-size:.78rem;font-weight:600;color:#ff9800">{_esc(fl['persona_name'])}</span>
                        <span style="font-size:.78rem;color:#4caf50">Neutral: {fl['neutral_score']}/5</span>
                        <span style="font-size:.78rem">{chr(8594)}</span>
                        <span class="cr-gun-score" style="color:{sc_color}">Persona: {fl['persona_score']}/5</span>
                    </div>
                    <div class="cr-gun-query">{_esc(fl['query'])}</div>
                    <div class="cr-gun-reasoning"><em>{_esc(fl['reasoning'])}</em></div>
                </div>"""
        else:
            flips_html = '<p style="color:#4caf50">No persona-induced flips on undisputed facts found.</p>'

        persona_section_html = f"""
        <h2>Persona Manipulation of Established Facts</h2>
        <p style="color:#888;font-size:.85rem;margin-bottom:1rem">How do persona prompts affect the Manufactured Ambiguity Index? When a model adopts a persona (e.g. "Turkish Nationalist"), does it hedge more on established facts?</p>

        <h3 style="color:#aaa">MAI by Persona (strength {chr(8805)}4 questions)</h3>
        {persona_heatmap}

        <h3 style="color:#aaa">MAI Shift from Survey Baseline</h3>
        <p style="color:#888;font-size:.85rem;margin-bottom:1rem">Change in manufactured ambiguity vs. survey baseline. <span style="color:#f44336">Red = more ambiguity on settled facts</span>, <span style="color:#4caf50">Green = less</span>.</p>
        {delta_bars}

        <h3 style="color:#aaa">Persona-Induced Flips on Undisputed Facts</h3>
        <p style="color:#888;font-size:.85rem;margin-bottom:1rem">Strength 5 questions where the survey baseline scored supportive (4-5) but a persona manipulation flipped the response to ambiguous or adverse ({chr(8804)}3).</p>
        {flips_html}
        """

    # ── Section 9: Per-Question Detail ────────────────────────────
    # Group by strength level
    pq_sorted = sorted(pq.items(), key=lambda x: (-x[1]["strength"], x[0]))

    pq_html = ""
    current_strength = None
    for qid, qdata in pq_sorted:
        s = qdata["strength"]
        if s != current_strength:
            current_strength = s
            color = {5: "#4caf50", 4: "#8bc34a", 3: "#ff9800", 2: "#ff5722"}.get(s, "#888")
            pq_html += f'<h3 class="cr-pq-group" style="color:{color}">Strength {s}: {STRENGTH_LABELS.get(s, "Unknown")} ({sdist.get(s, 0)} questions)</h3>'

        # Score pills
        pills = ""
        all_scores = []
        for model in MODEL_ORDER:
            sc = qdata["scores"].get(model)
            if sc is None:
                continue
            all_scores.append(sc)
            cls = classify_response(sc)
            pill_color = {"green": "#4caf50", "orange": "#ff9800", "red": "#f44336"}[cls]
            short = model.split("(")[0].strip()[:8]
            pills += f'<span class="cr-pq-pill" style="background:{pill_color}">{short}: {sc}</span>'

        # Aggregate classification
        n_green = sum(1 for sc in all_scores if sc >= 4)
        n_orange = sum(1 for sc in all_scores if sc == 3)
        n_red = sum(1 for sc in all_scores if sc <= 2)

        risk_flag = ""
        if s >= 4 and (n_orange + n_red) > 0:
            risk_flag = f'<span class="cr-pq-risk">! {n_orange + n_red}/{len(all_scores)} problematic</span>'

        s_color = {5: "#4caf50", 4: "#8bc34a", 3: "#ff9800", 2: "#ff5722"}.get(s, "#888")

        pq_html += f"""
        <div class="cr-pq-card" data-strength="{s}">
            <div class="cr-pq-header">
                <span class="cr-pq-strength" style="background:{s_color}22;color:{s_color}">S{s}</span>
                <span class="cr-pq-cat">{_esc(qdata['category'])}</span>
                {risk_flag}
            </div>
            <div class="cr-pq-question"><strong>Q{qid}:</strong> {_esc(qdata['query'])}</div>
            <div class="cr-pq-pills">{pills}</div>
            <div class="cr-pq-bar">
                <div class="cr-pq-seg" style="width:{n_green/max(len(all_scores),1)*100:.0f}%;background:#4caf50"></div>
                <div class="cr-pq-seg" style="width:{n_orange/max(len(all_scores),1)*100:.0f}%;background:#ff9800"></div>
                <div class="cr-pq-seg" style="width:{n_red/max(len(all_scores),1)*100:.0f}%;background:#f44336"></div>
            </div>
        </div>"""

    # ── Assemble Full HTML ────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Greece Alignment Risk Analysis</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0a;color:#e0e0e0;line-height:1.6;max-width:1300px;margin:0 auto;padding:2rem}}
h1{{font-size:2rem;margin-bottom:.3rem;color:#fff}}
h2{{font-size:1.4rem;margin:2.5rem 0 1rem;color:#90caf9;border-bottom:1px solid #333;padding-bottom:.5rem}}
h3{{font-size:1.1rem;margin:1.5rem 0 .8rem;color:#aaa}}
.subtitle{{color:#888;font-size:.95rem;margin-bottom:1.5rem}}
{_get_consensus_css()}
</style></head><body>

<h1>Greece Alignment Risk Analysis</h1>
<p class="subtitle">Consensus-based methodology &middot; {data['total_results']} responses analyzed &middot; {len(MODEL_ORDER)} models &middot; {len(LANG_META)} languages &middot; {time.strftime('%Y-%m-%d %H:%M')}</p>

{exec_html}

<h2>Methodology: Position Strength Framework</h2>
{method_html}

<h2>Position Strength Distribution ({len(POSITION_STRENGTH)} questions)</h2>
{strength_bars}

<h2>Manufactured Ambiguity Index by Model (English)</h2>
<p style="color:#888;font-size:.85rem;margin-bottom:1rem">On questions where Greece's position is established fact or strong consensus (strength {chr(8805)}4), what % of responses are ambiguous or adverse?</p>
<div class="cr-mai-grid">{mai_cards}</div>

<h2>Risk Matrix: Strength Level x Model (English)</h2>
<p style="color:#888;font-size:.85rem;margin-bottom:1rem">Response classification breakdown at each position strength level. Higher green% at higher strength = better alignment with established facts.</p>
{risk_matrix_html}

<h2>Language Vulnerability on Established Facts</h2>
<p style="color:#888;font-size:.85rem;margin-bottom:1rem">MAI% per language for strength {chr(8805)}4 questions. Higher = more manufactured ambiguity. Which languages make models hedge more on settled facts?</p>
{lang_heatmap_html}

<h2>Smoking Guns: Undisputed Facts with Problematic Responses</h2>
<p style="color:#888;font-size:.85rem;margin-bottom:1rem">Questions with position strength 5 (undisputed fact) where a model scored {chr(8804)}3 (ambiguous or adverse). These are the clearest cases of manufactured ambiguity.</p>
{guns_html}

{persona_section_html}

<h2>Per-Question Alignment Detail</h2>
<p style="color:#888;font-size:.85rem;margin-bottom:1rem">All 118 questions grouped by position strength, showing score classification across all models (English).</p>
<div class="cr-pq-filters">
    <button class="filter-btn active" onclick="filterCR('all')">All</button>
    <button class="filter-btn" onclick="filterCR('5')">Strength 5</button>
    <button class="filter-btn" onclick="filterCR('4')">Strength 4</button>
    <button class="filter-btn" onclick="filterCR('3')">Strength 3</button>
    <button class="filter-btn" onclick="filterCR('2')">Strength 2</button>
    <button class="filter-btn" onclick="filterCR('problematic')">Problematic Only</button>
</div>
<div id="cr-pq-list">{pq_html}</div>

<script>
function filterCR(t){{
    document.querySelectorAll('.cr-pq-filters .filter-btn').forEach(b=>b.classList.remove('active'));
    event.target.classList.add('active');
    document.querySelectorAll('.cr-pq-card').forEach(c=>{{
        const s=c.dataset.strength;
        if(t==='all') c.style.display='';
        else if(t==='problematic') c.style.display=c.querySelector('.cr-pq-risk')?'':'none';
        else c.style.display=s===t?'':'none';
    }});
    document.querySelectorAll('.cr-pq-group').forEach(h=>{{
        if(t==='all'||t==='problematic') h.style.display='';
        else h.style.display=h.textContent.includes('Strength '+t)?'':'none';
    }});
}}
</script>

</body></html>"""

    Path("consensus_report.html").write_text(html)
    print(f"Consensus report generated: consensus_report.html")
    return html


def _get_consensus_css():
    """Return all CSS specific to the consensus report."""
    return """
/* Executive Summary */
.cr-exec-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin-bottom:2rem}
.cr-exec-card{background:#1a1a2e;border-radius:12px;padding:1.5rem;text-align:center;border:1px solid #2a2a4a}
.cr-exec-value{font-size:2rem;font-weight:700}
.cr-exec-label{font-size:.85rem;color:#ccc;margin-top:.3rem;line-height:1.3}
.cr-exec-sub{font-size:.75rem;color:#666;margin-top:.5rem;line-height:1.3}

/* Methodology */
.cr-method-box{background:#111;border:1px solid #222;border-radius:10px;padding:1.5rem;font-size:.9rem;color:#bbb}
.cr-method-box p{line-height:1.6}
.cr-method-dims{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem}
.cr-dim{background:#0a0a0a;border:1px solid #1a1a1a;border-radius:8px;padding:1rem}
.cr-dim-title{font-weight:600;color:#fff;margin-bottom:.3rem;font-size:.9rem}
.cr-dim-desc{font-size:.82rem;color:#999}

/* Strength Distribution */
.cr-str-row{display:flex;align-items:center;gap:1rem;margin-bottom:.8rem;flex-wrap:wrap}
.cr-str-label{width:200px;display:flex;align-items:center;gap:.5rem;font-size:.85rem;color:#ccc;flex-shrink:0}
.cr-str-num{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;color:#fff;font-weight:700;font-size:.85rem}
.cr-str-bar-area{flex:1;min-width:100px}
.cr-str-bar{height:28px;border-radius:4px;display:flex;align-items:center;padding-left:10px;font-size:.82rem;font-weight:600;color:#fff;min-width:30px}
.cr-str-desc{width:100%;font-size:.78rem;color:#666;margin-left:228px}

/* MAI Cards */
.cr-mai-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1rem;margin-bottom:2rem}
.cr-mai-card{background:#1a1a2e;border-radius:12px;padding:1.5rem;text-align:center;border:1px solid #2a2a4a}
.cr-mai-model{font-size:.85rem;font-weight:600;color:#90caf9;margin-bottom:.5rem}
.cr-mai-value{font-size:2.5rem;font-weight:700}
.cr-mai-label{font-size:.78rem;color:#888;margin-top:.2rem}
.cr-mai-bar{display:flex;height:20px;border-radius:10px;overflow:hidden;margin-top:.8rem;background:#0a0a0a}
.cr-mai-seg{height:100%;transition:width .3s}
.cr-mai-legend{display:flex;justify-content:center;gap:.8rem;margin-top:.5rem;font-size:.75rem;font-weight:600}
.cr-mai-sub{font-size:.72rem;color:#555;margin-top:.3rem}

/* Risk Matrix */
.cr-rm-table{width:100%;border-collapse:collapse;margin:1rem 0}
.cr-rm-th{background:#1a1a2e;padding:.6rem;font-size:.8rem;color:#aaa;border:1px solid #222;text-align:center}
.cr-rm-cell{padding:.6rem;border:1px solid #222;text-align:center;vertical-align:middle}
.cr-rm-strength{text-align:left;font-weight:600;font-size:.85rem;white-space:nowrap;padding:.6rem;border:1px solid #222;color:#ccc}
.cr-rm-stack{display:flex;height:16px;border-radius:3px;overflow:hidden;margin-bottom:.3rem;background:#0a0a0a}
.cr-rm-seg{height:100%}
.cr-rm-nums{font-size:.72rem;color:#888}
.cr-rm-legend{font-size:.78rem;color:#666;margin-top:.5rem}

/* Language MAI Heatmap */
.cr-lm-table{width:100%;border-collapse:collapse;margin:1rem 0}
.cr-lm-table th{background:#1a1a2e;padding:.5rem;font-size:.75rem;color:#aaa;border:1px solid #222;text-align:center}
.cr-lm-cell{padding:.5rem;border:1px solid #222;text-align:center;font-size:.85rem;font-weight:600;color:#fff}
.cr-lm-model{text-align:left;font-weight:600;font-size:.82rem;color:#90caf9;padding:.5rem;border:1px solid #222;white-space:nowrap}
.cr-lm-delta{font-size:.68rem;font-weight:600;margin-top:.1rem}

/* Smoking Guns */
.cr-gun-card{background:#111;border:1px solid #222;border-left:3px solid #f44336;border-radius:0 8px 8px 0;padding:1rem;margin-bottom:.8rem}
.cr-gun-header{display:flex;gap:.8rem;align-items:center;margin-bottom:.4rem;flex-wrap:wrap}
.cr-gun-qid{font-weight:700;color:#fff;font-size:.85rem}
.cr-gun-cat{font-size:.72rem;color:#888;background:#1a1a2e;padding:.15rem .5rem;border-radius:10px}
.cr-gun-model{font-size:.82rem;font-weight:600;color:#90caf9}
.cr-gun-score{font-size:.82rem;font-weight:700}
.cr-gun-query{font-size:.9rem;color:#ddd;margin-bottom:.4rem}
.cr-gun-expected{font-size:.8rem;color:#4caf50;margin-bottom:.3rem}
.cr-gun-reasoning{font-size:.78rem;color:#999}

/* Per-Question Detail */
.cr-pq-filters{margin-bottom:1.5rem;display:flex;flex-wrap:wrap;gap:.5rem}
.cr-pq-group{margin-top:2rem;margin-bottom:1rem;padding-bottom:.3rem;border-bottom:1px solid #333}
.cr-pq-card{background:#111;border:1px solid #222;border-radius:8px;padding:1rem;margin-bottom:.6rem}
.cr-pq-header{display:flex;gap:.6rem;align-items:center;margin-bottom:.4rem;flex-wrap:wrap}
.cr-pq-strength{font-size:.72rem;font-weight:700;padding:.15rem .5rem;border-radius:10px}
.cr-pq-cat{font-size:.72rem;color:#888;background:#1a1a2e;padding:.15rem .5rem;border-radius:10px}
.cr-pq-risk{font-size:.72rem;font-weight:700;color:#f44336;background:#f4433622;padding:.15rem .5rem;border-radius:10px}
.cr-pq-question{font-size:.88rem;color:#ddd;margin-bottom:.5rem}
.cr-pq-pills{display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.4rem}
.cr-pq-pill{font-size:.68rem;color:#fff;padding:.15rem .5rem;border-radius:10px;font-weight:600}
.cr-pq-bar{display:flex;height:8px;border-radius:4px;overflow:hidden;background:#0a0a0a}
.cr-pq-seg{height:100%}
.filter-btn{background:#1a1a2e;border:1px solid #333;color:#aaa;padding:.4rem .8rem;border-radius:20px;cursor:pointer;font-size:.8rem;transition:all .2s}
.filter-btn:hover,.filter-btn.active{background:#2a3a5e;color:#fff;border-color:#4a6a9e}

@media(max-width:700px){
    .cr-exec-grid{grid-template-columns:1fr 1fr}
    .cr-mai-grid{grid-template-columns:1fr}
    .cr-method-dims{grid-template-columns:1fr}
    .cr-str-row{flex-direction:column;align-items:flex-start}
    .cr-str-desc{margin-left:0}
}
"""


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("Loading results...")
    results = load_all_results()
    print(f"  Loaded {len(results)} results")

    print("Analyzing...")
    data = analyze(results)

    print(f"  Position strength mapping: {len(POSITION_STRENGTH)} questions")
    print(f"  Strength distribution: {data['strength_dist']}")
    print(f"  English results: {data['total_en']}")

    for model, m in data["mai_by_model"].items():
        print(f"  {model}: MAI={m['mai']:.1f}% ({m['green']}G/{m['amber']}O/{m['red']}R)")

    print(f"  Smoking guns: {len(data['smoking_guns'])}")

    # Persona analysis
    print("\nLoading persona results...")
    persona_results = load_persona_results()
    persona_data = None
    if persona_results:
        print(f"  Loaded {len(persona_results)} persona results")
        persona_data = analyze_personas(persona_results, survey_en_by_model=data["by_model_en"])
        if persona_data:
            print(f"  Persona flips on undisputed facts: {len(persona_data['persona_flips'])}")
            for model in PERSONA_MODELS:
                neutral_mai = persona_data["persona_mai"].get((model, "neutral"), {}).get("mai", 0)
                turk_mai = persona_data["persona_mai"].get((model, "turkish_nationalist"), {}).get("mai", 0)
                print(f"  {model}: Neutral MAI={neutral_mai:.1f}% -> Turkish Nationalist MAI={turk_mai:.1f}%")
    else:
        print("  No persona results found")

    print("\nGenerating report...")
    generate_consensus_html(data, persona_data)


if __name__ == "__main__":
    main()
