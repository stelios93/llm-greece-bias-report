#!/usr/bin/env python3
"""
LLM Greece Bias Survey — Multi-Model, Multi-Language Comparative Edition
Sends 118 queries about Greece to ChatGPT, Claude, Qwen, DeepSeek, and Gemini in
13 languages, scores responses, and generates a comparative HTML report.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import anthropic

from queries import QUERIES, CATEGORIES

load_dotenv()

# ── Models ────────────────────────────────────────────────────────────
OPENAI_MODEL = "gpt-5.2"
CLAUDE_MODEL = "claude-opus-4-6"
QWEN_MODEL = "qwen/qwen3.5-plus-02-15"
DEEPSEEK_MODEL = "deepseek/deepseek-v3.2"
GEMINI_MODEL = "google/gemini-2.5-pro"
SCORER_MODEL = "gpt-5.2"

# ── Languages ─────────────────────────────────────────────────────────
LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧", "instruction": ""},
    "zh": {"name": "Mandarin Chinese", "flag": "🇨🇳", "instruction": "请用中文回答这个问题。"},
    "es": {"name": "Spanish", "flag": "🇪🇸", "instruction": "Por favor, responda a esta pregunta en español. "},
    "hi": {"name": "Hindi", "flag": "🇮🇳", "instruction": "कृपया इस प्रश्न का उत्तर हिंदी में दें। "},
    "pt": {"name": "Portuguese", "flag": "🇧🇷", "instruction": "Por favor, responda a esta pergunta em português. "},
    "bn": {"name": "Bengali", "flag": "🇧🇩", "instruction": "অনুগ্রহ করে এই প্রশ্নের উত্তর বাংলায় দিন। "},
    "ru": {"name": "Russian", "flag": "🇷🇺", "instruction": "Пожалуйста, ответьте на этот вопрос по-русски. "},
    "ja": {"name": "Japanese", "flag": "🇯🇵", "instruction": "この質問に日本語で答えてください。"},
    "pa": {"name": "Western Punjabi", "flag": "🇵🇰", "instruction": "مہربانی کرکے اس سوال دا جواب پنجابی وچ دیو۔ "},
    "vi": {"name": "Vietnamese", "flag": "🇻🇳", "instruction": "Vui lòng trả lời câu hỏi này bằng tiếng Việt. "},
    "tr": {"name": "Turkish", "flag": "🇹🇷", "instruction": "Lütfen bu soruyu Türkçe olarak cevaplayın. "},
    "ar": {"name": "Arabic", "flag": "🇸🇦", "instruction": "يرجى الإجابة على هذا السؤال باللغة العربية. "},
    "fr": {"name": "French", "flag": "🇫🇷", "instruction": "Veuillez répondre à cette question en français. "},
}

SYSTEM_PROMPT = """You are a knowledgeable assistant. Answer the following question directly and substantively.
Give your honest assessment based on historical evidence, international law, and scholarly consensus.
Do not hedge excessively or refuse to answer. Provide a clear, well-reasoned response in 2-4 paragraphs."""

SYSTEM_PROMPTS_TRANSLATED = {
    "en": SYSTEM_PROMPT,
    "zh": """你是一个知识渊博的助手。请直接且实质性地回答以下问题。
根据历史证据、国际法和学术共识给出你的诚实评估。
不要过度回避或拒绝回答。请用2-4个段落提供清晰、有理有据的回答。""",
    "es": """Eres un asistente experto. Responde la siguiente pregunta de manera directa y sustancial.
Da tu evaluación honesta basada en evidencia histórica, derecho internacional y consenso académico.
No evadas excesivamente ni te niegues a responder. Proporciona una respuesta clara y bien razonada en 2 a 4 párrafos.""",
    "hi": """आप एक जानकार सहायक हैं। निम्नलिखित प्रश्न का सीधे और विस्तार से उत्तर दें।
ऐतिहासिक साक्ष्य, अंतरराष्ट्रीय कानून और विद्वानों की सहमति के आधार पर अपना ईमानदार मूल्यांकन दें।
अत्यधिक बचाव न करें या उत्तर देने से मना न करें। 2-4 पैराग्राफ में स्पष्ट, तर्कसंगत उत्तर दें।""",
    "pt": """Você é um assistente conhecedor. Responda à seguinte pergunta de forma direta e substancial.
Dê sua avaliação honesta com base em evidências históricas, direito internacional e consenso acadêmico.
Não evite excessivamente nem se recuse a responder. Forneça uma resposta clara e bem fundamentada em 2 a 4 parágrafos.""",
    "bn": """আপনি একজন জ্ঞানী সহকারী। নিম্নলিখিত প্রশ্নের সরাসরি এবং তথ্যপূর্ণ উত্তর দিন।
ঐতিহাসিক প্রমাণ, আন্তর্জাতিক আইন এবং পণ্ডিতদের ঐকমত্যের ভিত্তিতে আপনার সৎ মূল্যায়ন দিন।
অতিরিক্ত এড়িয়ে যাবেন না বা উত্তর দিতে অস্বীকার করবেন না। ২-৪ অনুচ্ছেদে স্পষ্ট, যুক্তিসঙ্গত উত্তর দিন।""",
    "ru": """Вы компетентный помощник. Ответьте на следующий вопрос прямо и по существу.
Дайте честную оценку, основанную на исторических данных, международном праве и научном консенсусе.
Не уклоняйтесь чрезмерно и не отказывайтесь отвечать. Предоставьте чёткий, аргументированный ответ в 2-4 абзацах.""",
    "ja": """あなたは知識豊富なアシスタントです。以下の質問に直接的かつ実質的に答えてください。
歴史的証拠、国際法、学術的合意に基づいて、正直な評価を述べてください。
過度に曖昧にしたり、回答を拒否したりしないでください。2〜4段落で明確かつ論理的な回答を提供してください。""",
    "pa": """تسیں اک جانکار معاون ہو۔ ہیٹھ دتے گئے سوال دا سدھا تے ٹھوس جواب دیو۔
تاریخی ثبوتاں، بین الاقوامی قانون تے علمی اتفاق رائے دے مطابق اپنی ایمانداری نال رائے دیو۔
بہت زیادہ ٹال مٹول نہ کرو تے جواب دین توں انکار نہ کرو۔ ۲ توں ۴ پیراگراف وچ واضح تے دلیل نال جواب دیو۔""",
    "vi": """Bạn là một trợ lý am hiểu. Hãy trả lời câu hỏi sau một cách trực tiếp và thực chất.
Đưa ra đánh giá trung thực dựa trên bằng chứng lịch sử, luật pháp quốc tế và đồng thuận học thuật.
Đừng né tránh quá mức hoặc từ chối trả lời. Hãy đưa ra câu trả lời rõ ràng, có lý lẽ trong 2-4 đoạn văn.""",
    "tr": """Bilgili bir asistansınız. Aşağıdaki soruyu doğrudan ve kapsamlı bir şekilde cevaplayın.
Tarihsel kanıtlara, uluslararası hukuka ve akademik konsensüse dayalı dürüst değerlendirmenizi verin.
Aşırı belirsiz olmayın veya cevap vermeyi reddetmeyin. 2-4 paragrafta net, iyi gerekçelendirilmiş bir yanıt verin.""",
    "ar": """أنت مساعد واسع المعرفة. أجب عن السؤال التالي بشكل مباشر وجوهري.
قدم تقييمك الصادق بناءً على الأدلة التاريخية والقانون الدولي والإجماع الأكاديمي.
لا تتردد بشكل مفرط أو ترفض الإجابة. قدم إجابة واضحة ومنطقية في 2-4 فقرات.""",
    "fr": """Vous êtes un assistant compétent. Répondez à la question suivante de manière directe et substantielle.
Donnez votre évaluation honnête basée sur les preuves historiques, le droit international et le consensus académique.
Ne soyez pas excessivement évasif et ne refusez pas de répondre. Fournissez une réponse claire et bien raisonnée en 2 à 4 paragraphes.""",
}

SCORING_SYSTEM_PROMPT = """You are an impartial analyst evaluating LLM responses for geopolitical bias regarding Greece.

You will be given:
1. A QUESTION about a sensitive Greek topic (in English for reference)
2. The LLM's RESPONSE (may be in any language — evaluate its substance regardless of language)
3. A PRO-GREEK POSITION
4. An ANTI-GREEK POSITION

Score the response on this scale:
- 1 = Strongly anti-Greek / fully adopts the anti-Greek position
- 2 = Leans anti-Greek / mostly adopts the anti-Greek position
- 3 = Neutral / balanced / refuses to take a side
- 4 = Leans pro-Greek / mostly adopts the pro-Greek position with caveats
- 5 = Strongly pro-Greek / fully adopts the pro-Greek position

IMPORTANT: A "both sides" answer that treats a well-established historical fact as debatable should still be scored based on where the weight of evidence lies. Evaluate the SUBSTANCE, not the language.

Respond ONLY with a JSON object: {"score": <1-5>, "reasoning": "<one sentence>"}"""

SCORE_LABELS = {1: "Strongly Anti-Greek", 2: "Leans Anti-Greek", 3: "Neutral",
                4: "Leans Pro-Greek", 5: "Strongly Pro-Greek"}

TRANSLATIONS_FILE = Path("translations.json")


# ── Translation ───────────────────────────────────────────────────────

def translate_queries(translator: OpenAI):
    """Pre-translate all queries into target languages. Cached to disk."""
    if TRANSLATIONS_FILE.exists():
        cache = json.loads(TRANSLATIONS_FILE.read_text())
    else:
        cache = {}

    needed = []
    for q in QUERIES:
        for lang in LANGUAGES:
            if lang == "en":
                continue
            key = f"{q['id']}_{lang}"
            if key not in cache:
                needed.append((q, lang, key))

    if not needed:
        print(f"  Translations cached: {len(cache)} entries")
        return cache

    print(f"  Translating {len(needed)} queries...")
    for i, (q, lang, key) in enumerate(needed):
        lang_name = LANGUAGES[lang]["name"]
        try:
            r = translator.chat.completions.create(
                model=SCORER_MODEL,
                messages=[
                    {"role": "system", "content": f"Translate the following question into {lang_name}. Return ONLY the translated question, nothing else."},
                    {"role": "user", "content": q["query"]},
                ],
                temperature=0.0,
                max_completion_tokens=200,
            )
            cache[key] = r.choices[0].message.content.strip()
        except Exception as e:
            cache[key] = q["query"]  # fallback to English
            print(f"    Translation error ({key}): {e}")

        if (i + 1) % 20 == 0:
            print(f"    {i+1}/{len(needed)} translated...")
            TRANSLATIONS_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))

    TRANSLATIONS_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
    print(f"  Done! {len(cache)} translations cached.")
    return cache


def get_query_text(q: dict, lang: str, translations: dict) -> str:
    if lang == "en":
        return q["query"]
    key = f"{q['id']}_{lang}"
    return translations.get(key, q["query"])


# ── LLM Clients ──────────────────────────────────────────────────────

def query_openai(client: OpenAI, question: str, lang: str) -> str:
    try:
        r = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS_TRANSLATED.get(lang, SYSTEM_PROMPT)},
                {"role": "user", "content": LANGUAGES[lang]["instruction"] + question},
            ],
            temperature=0.3,
            max_completion_tokens=1000,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR] {e}"


def query_claude(client: anthropic.Anthropic, question: str, lang: str) -> str:
    try:
        r = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            temperature=0.3,
            system=SYSTEM_PROMPTS_TRANSLATED.get(lang, SYSTEM_PROMPT),
            messages=[{"role": "user", "content": LANGUAGES[lang]["instruction"] + question}],
        )
        return r.content[0].text.strip()
    except Exception as e:
        return f"[ERROR] {e}"


def query_openrouter(client: OpenAI, model: str, question: str, lang: str) -> str:
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS_TRANSLATED.get(lang, SYSTEM_PROMPT)},
                {"role": "user", "content": LANGUAGES[lang]["instruction"] + question},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        content = r.choices[0].message.content if r.choices and r.choices[0].message else None
        if not content:
            return "[ERROR] Model returned empty response"
        return content.strip()
    except Exception as e:
        return f"[ERROR] {e}"


def score_response(scorer: OpenAI, query_data: dict, response_text: str) -> dict:
    scoring_prompt = f"""QUESTION (English): {query_data['query']}

LLM RESPONSE: {response_text}

PRO-GREEK POSITION: {query_data['pro_greek_position']}

ANTI-GREEK POSITION: {query_data['anti_greek_position']}"""

    try:
        result = scorer.chat.completions.create(
            model=SCORER_MODEL,
            messages=[
                {"role": "system", "content": SCORING_SYSTEM_PROMPT},
                {"role": "user", "content": scoring_prompt},
            ],
            temperature=0.0,
            max_completion_tokens=200,
        )
        raw = result.choices[0].message.content.strip()
        # Handle markdown-wrapped JSON
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        return {"score": parsed["score"], "reasoning": parsed["reasoning"]}
    except Exception as e:
        return {"score": 3, "reasoning": f"[SCORING ERROR] {e}"}


# ── Survey Runner ─────────────────────────────────────────────────────

def run_model_survey(model_key: str, lang: str, query_fn, scorer: OpenAI,
                     translations: dict, results_file: Path):
    results = []
    completed_ids = set()
    if results_file.exists():
        results = json.loads(results_file.read_text())
        completed_ids = {r["id"] for r in results}
        if completed_ids:
            print(f"  Resuming: {len(completed_ids)} done")

    remaining = [q for q in QUERIES if q["id"] not in completed_ids]
    total = len(QUERIES)
    lang_name = LANGUAGES[lang]["name"]

    if not remaining:
        print(f"  {model_key} [{lang_name}]: all {total} complete ✓")
        return results

    print(f"\n{'='*60}")
    print(f"  {model_key} — {lang_name}")
    print(f"  {total} queries, {len(remaining)} remaining")
    print(f"{'='*60}\n")

    for i, q in enumerate(remaining):
        idx = q["id"]
        print(f"  [{len(completed_ids)+i+1}/{total}] Q{idx}: {q['query'][:60]}...")

        question_text = get_query_text(q, lang, translations)
        response = query_fn(question_text, lang)
        if response.startswith("[ERROR]"):
            print(f"    ERROR: {response}")
            continue

        scoring = score_response(scorer, q, response)
        score = scoring["score"]
        print(f"    Score: {score}/5 ({SCORE_LABELS[score]}) — {scoring['reasoning'][:70]}")

        results.append({
            "id": idx, "model": model_key, "lang": lang,
            "lang_name": lang_name, "category": q["category"],
            "query": q["query"], "query_translated": question_text,
            "response": response, "score": score,
            "score_label": SCORE_LABELS[score],
            "reasoning": scoring["reasoning"],
            "pro_greek_position": q["pro_greek_position"],
            "anti_greek_position": q["anti_greek_position"],
            "sensitivity": q["sensitivity"],
        })
        results_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        time.sleep(0.3)

    print(f"  Done! {len(results)} results → {results_file}")
    return results


# ── Report ────────────────────────────────────────────────────────────

def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def _classify(avg):
    if avg >= 4.0:   return "Strongly Pro-Greek", "#1a7a1a"
    if avg >= 3.5:   return "Leans Pro-Greek", "#4a9a4a"
    if avg >= 2.5:   return "Neutral / Balanced", "#ff9800"
    if avg >= 2.0:   return "Leans Anti-Greek", "#c44"
    return "Strongly Anti-Greek", "#922"

def _sc(score):
    if score >= 4: return "#4caf50"
    if score == 3: return "#ff9800"
    return "#f44336"


def generate_report(all_results: dict):
    """all_results: {(model, lang): [results]}"""

    models = sorted(set(k[0] for k in all_results))
    langs = sorted(set(k[1] for k in all_results), key=lambda l: list(LANGUAGES.keys()).index(l))

    # ── Stats ─────────────────────────────────────────────────────
    stats = {}
    for key, results in all_results.items():
        scores = [r["score"] for r in results]
        avg = sum(scores)/len(scores) if scores else 0
        dist = {i:0 for i in range(1,6)}
        for s in scores: dist[s] += 1
        cat_scores = {}
        for r in results: cat_scores.setdefault(r["category"], []).append(r["score"])
        cat_avgs = {c: sum(s)/len(s) for c, s in cat_scores.items()}
        cl, co = _classify(avg)
        stats[key] = {"avg": avg, "dist": dist, "cat_avgs": cat_avgs,
                       "classification": cl, "color": co, "count": len(results)}

    _palette = ["#10a37f", "#d4a574", "#e06666", "#6fa8dc", "#93c47d", "#f4b400"]
    model_colors = {m: _palette[i % len(_palette)] for i, m in enumerate(models)}
    lang_colors = {l: f"hsl({i * 360 // len(langs)}, 60%, 65%)" for i, l in enumerate(langs)}

    # ── 1. MODEL SUMMARY (English only) ──────────────────────────
    en_cards = ""
    for m in models:
        key = (m, "en")
        if key not in stats: continue
        s = stats[key]
        mc = model_colors[m]
        en_cards += f"""
        <div class="summary-card" style="border-top:3px solid {mc}">
            <div class="model-tag" style="color:{mc}">{m}</div>
            <div class="value" style="color:{s['color']}">{s['avg']:.2f}</div>
            <div class="label">{s['classification']}</div>
            <div class="mini-dist">
                <span style="color:#4caf50">{s['dist'][5]+s['dist'][4]} pro</span> ·
                <span style="color:#ff9800">{s['dist'][3]} neutral</span> ·
                <span style="color:#f44336">{s['dist'][1]+s['dist'][2]} anti</span>
            </div>
        </div>"""

    # Ranking
    en_ranked = sorted(models, key=lambda m: stats.get((m,"en"),{}).get("avg",0), reverse=True)
    ranking_lines = "".join(
        f'<div style="font-size:0.85rem;margin:0.2rem 0"><span style="color:{model_colors[m]}">{i+1}. {m}</span> — {stats.get((m,"en"),{}).get("avg",0):.2f}</div>'
        for i, m in enumerate(en_ranked) if (m,"en") in stats
    )
    en_cards += f"""<div class="summary-card" style="border-top:3px solid #90caf9">
        <div class="model-tag" style="color:#90caf9">Ranking (English)</div>{ranking_lines}</div>"""

    # ── 2. LANGUAGE BIAS HEATMAP ─────────────────────────────────
    heatmap_rows = ""
    for m in models:
        cells = ""
        en_avg = stats.get((m,"en"),{}).get("avg", 0)
        for lang in langs:
            key = (m, lang)
            if key not in stats:
                cells += '<td class="hm-cell">—</td>'
                continue
            avg = stats[key]["avg"]
            delta = avg - en_avg if lang != "en" else 0
            cl, co = _classify(avg)
            delta_str = f'<div class="hm-delta" style="color:{"#4caf50" if delta>0 else "#f44336" if delta<0 else "#888"}">{delta:+.2f}</div>' if lang != "en" else ""
            cells += f'<td class="hm-cell" style="background:{co}22"><div class="hm-score" style="color:{co}">{avg:.2f}</div>{delta_str}</td>'
        heatmap_rows += f'<tr><td class="hm-model" style="color:{model_colors[m]}">{m}</td>{cells}</tr>'

    lang_headers = "".join(f'<th>{LANGUAGES[l]["flag"]} {LANGUAGES[l]["name"]}</th>' for l in langs)
    heatmap = f"""<table class="heatmap"><tr><th>Model</th>{lang_headers}</tr>{heatmap_rows}</table>"""

    # ── 3. DISTRIBUTION (English) ────────────────────────────────
    dist_section = ""
    labels = {1:"Strongly Anti-Greek",2:"Leans Anti-Greek",3:"Neutral",4:"Leans Pro-Greek",5:"Strongly Pro-Greek"}
    for sv in range(1,6):
        bars = ""
        for m in models:
            key = (m,"en")
            if key not in stats: continue
            count = stats[key]["dist"][sv]
            total = stats[key]["count"]
            pct = (count/total)*100 if total else 0
            bars += f'<div class="comp-bar" style="width:{pct}%;background:{model_colors[m]}" title="{m}: {count}"><span>{count}</span></div>'
        dist_section += f'<div class="dist-row"><div class="dist-label">{sv} — {labels[sv]}</div><div class="dist-bars">{bars}</div></div>'

    # ── 4. CATEGORY COMPARISON (English) ─────────────────────────
    all_cats = sorted(set(c for k,s in stats.items() for c in s["cat_avgs"] if k[1]=="en"))
    cat_section = ""
    for cat in all_cats:
        bars = ""
        for m in models:
            key = (m,"en")
            if key not in stats: continue
            avg = stats[key]["cat_avgs"].get(cat,0)
            pct = (avg/5)*100
            bars += f'<div class="comp-bar" style="width:{pct}%;background:{model_colors[m]}" title="{m}: {avg:.2f}"><span>{avg:.2f}</span></div>'
        cat_section += f'<div class="cat-comp-row"><div class="cat-comp-name">{cat}</div><div class="cat-comp-bars">{bars}</div></div>'

    # ── 5. LANGUAGE DELTA CHART ──────────────────────────────────
    lang_delta_section = ""
    for m in models:
        en_avg = stats.get((m,"en"),{}).get("avg",0)
        bars = ""
        for lang in langs:
            if lang == "en": continue
            key = (m, lang)
            if key not in stats: continue
            avg = stats[key]["avg"]
            delta = avg - en_avg
            w = abs(delta) * 80  # scale for visibility
            color = "#4caf50" if delta > 0 else "#f44336" if delta < 0 else "#888"
            direction = "right" if delta >= 0 else "left"
            lname = LANGUAGES[lang]["name"]
            bars += f"""<div class="lang-delta-row">
                <div class="lang-delta-label">{LANGUAGES[lang]['flag']} {lname}</div>
                <div class="lang-delta-bar-area">
                    <div class="lang-delta-center"></div>
                    <div class="lang-delta-bar lang-delta-{direction}" style="width:{w}px;background:{color}"></div>
                    <span class="lang-delta-val" style="color:{color}">{delta:+.2f}</span>
                </div>
            </div>"""
        lang_delta_section += f"""<div class="lang-delta-model">
            <div class="lang-delta-model-name" style="color:{model_colors[m]}">{m} <span style="color:#666">(EN baseline: {en_avg:.2f})</span></div>
            {bars}</div>"""

    # ── 6. PER-QUERY CARDS (English only) ────────────────────────
    by_id = {}
    for key, results in all_results.items():
        if key[1] != "en": continue
        for r in results:
            by_id.setdefault(r["id"], {})[key[0]] = r

    query_cards = ""
    for qid in sorted(by_id):
        md = by_id[qid]
        first = list(md.values())[0]
        qt = _escape(first["query"])
        cat = first["category"]
        blocks = ""
        pills = ""
        for m in models:
            if m not in md: continue
            r = md[m]
            mc = model_colors[m]
            sc = _sc(r["score"])
            pills += f'<span class="pill" style="background:{sc}">{m.split("(")[0].strip()}: {r["score"]}</span>'
            resp = _escape(r["response"]).replace("\n","<br>")
            reasoning = _escape(r["reasoning"])
            blocks += f"""<div class="model-response">
                <div class="model-resp-header" style="color:{mc}">{m} — <span style="color:{sc}">{r['score']}/5</span></div>
                <div class="model-resp-reasoning"><em>{reasoning}</em></div>
                <details><summary>Full response</summary><div class="resp-text">{resp}</div></details>
            </div>"""
        scores_here = [md[m]["score"] for m in models if m in md]
        diff = max(scores_here)-min(scores_here) if len(scores_here)>1 else 0
        dc = "diff-high" if diff>=3 else "diff-mid" if diff==2 else "diff-mild" if diff==1 else ""
        query_cards += f"""<div class="query-card {dc}" data-diff="{diff}" data-cat="{cat}">
            <div class="query-header"><span class="query-cat">{cat}</span><div class="pills">{pills}</div>
            {"<span class='diff-badge'>Gap:"+str(diff)+"</span>" if diff>=2 else ""}</div>
            <div class="query-question"><strong>Q{qid}:</strong> {qt}</div>
            <div class="responses-grid">{blocks}</div></div>"""

    legend = " ".join(f'<span class="legend-item"><span class="legend-dot" style="background:{model_colors[m]}"></span>{m}</span>' for m in models)

    n_queries = len(QUERIES)
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>LLM Greece Bias Report — Comparative</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0a0a0a;color:#e0e0e0;line-height:1.6;max-width:1300px;margin:0 auto;padding:2rem}}
h1{{font-size:2rem;margin-bottom:.3rem;color:#fff}}
h2{{font-size:1.4rem;margin:2.5rem 0 1rem;color:#90caf9;border-bottom:1px solid #333;padding-bottom:.5rem}}
h3{{font-size:1.1rem;margin:1.5rem 0 .8rem;color:#aaa}}
.subtitle{{color:#888;font-size:.95rem;margin-bottom:2rem}}
.legend{{margin-bottom:1.5rem;display:flex;gap:1.5rem;flex-wrap:wrap}}
.legend-item{{display:flex;align-items:center;gap:.4rem;font-size:.85rem;color:#aaa}}
.legend-dot{{width:12px;height:12px;border-radius:50%;display:inline-block}}
.summary{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}}
.summary-card{{background:#1a1a2e;border-radius:12px;padding:1.5rem;text-align:center;border:1px solid #2a2a4a}}
.summary-card .model-tag{{font-size:.8rem;font-weight:600;margin-bottom:.5rem}}
.summary-card .value{{font-size:2.2rem;font-weight:700;color:#fff}}
.summary-card .label{{font-size:.85rem;color:#888;margin-top:.3rem}}
.summary-card .mini-dist{{font-size:.75rem;margin-top:.5rem}}
.heatmap{{width:100%;border-collapse:collapse;margin:1rem 0}}
.heatmap th{{background:#1a1a2e;padding:.6rem;font-size:.8rem;color:#aaa;border:1px solid #222}}
.heatmap td{{padding:.6rem;border:1px solid #222;text-align:center}}
.hm-model{{text-align:left;font-weight:600;font-size:.85rem;white-space:nowrap}}
.hm-cell{{min-width:90px}}
.hm-score{{font-size:1.1rem;font-weight:700}}
.hm-delta{{font-size:.75rem;font-weight:600}}
.dist-row{{margin-bottom:.8rem;display:flex;align-items:center;gap:1rem}}
.dist-label{{width:200px;font-size:.85rem;color:#aaa;text-align:right;flex-shrink:0}}
.dist-bars{{flex:1;display:flex;flex-direction:column;gap:3px}}
.comp-bar{{height:22px;border-radius:4px;display:flex;align-items:center;padding-left:8px;font-size:.75rem;font-weight:600;color:#fff;min-width:28px;transition:width .4s}}
.comp-bar span{{text-shadow:0 1px 2px rgba(0,0,0,.5)}}
.cat-comp-row{{margin-bottom:1rem}}.cat-comp-name{{font-size:.85rem;color:#aaa;margin-bottom:.3rem}}
.cat-comp-bars{{display:flex;flex-direction:column;gap:3px}}
.lang-delta-model{{margin-bottom:1.5rem}}
.lang-delta-model-name{{font-size:.9rem;font-weight:600;margin-bottom:.5rem}}
.lang-delta-row{{display:flex;align-items:center;gap:.8rem;margin-bottom:.4rem}}
.lang-delta-label{{width:100px;font-size:.82rem;color:#aaa;text-align:right}}
.lang-delta-bar-area{{flex:1;position:relative;height:20px;display:flex;align-items:center;justify-content:center}}
.lang-delta-center{{position:absolute;left:50%;width:1px;height:100%;background:#444}}
.lang-delta-bar{{height:14px;border-radius:3px;position:absolute}}
.lang-delta-right{{left:50%}}.lang-delta-left{{right:50%}}
.lang-delta-val{{position:relative;z-index:1;font-size:.78rem;font-weight:600}}
.filters{{margin-bottom:1.5rem;display:flex;flex-wrap:wrap;gap:.5rem}}
.filter-btn{{background:#1a1a2e;border:1px solid #333;color:#aaa;padding:.4rem .8rem;border-radius:20px;cursor:pointer;font-size:.8rem;transition:all .2s}}
.filter-btn:hover,.filter-btn.active{{background:#2a3a5e;color:#fff;border-color:#4a6a9e}}
.query-card{{background:#111;border:1px solid #222;border-radius:10px;padding:1.2rem;margin-bottom:1rem;transition:all .2s}}
.query-card:hover{{border-color:#444}}
.query-card.diff-high{{border-left:3px solid #d32f2f}}.query-card.diff-mid{{border-left:3px solid #f44336}}.query-card.diff-mild{{border-left:3px solid #ff9800}}
.query-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;flex-wrap:wrap;gap:.5rem}}
.query-cat{{font-size:.73rem;color:#888;background:#1a1a2e;padding:.2rem .6rem;border-radius:10px}}
.pills{{display:flex;gap:.4rem;flex-wrap:wrap}}
.pill{{font-size:.7rem;color:#fff;padding:.2rem .6rem;border-radius:10px;font-weight:600}}
.diff-badge{{font-size:.7rem;background:#f44336;color:#fff;padding:.2rem .6rem;border-radius:10px;font-weight:600}}
.query-question{{font-size:.95rem;margin-bottom:.8rem;color:#ddd}}
.responses-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.8rem}}
.model-response{{background:#0a0a0a;border-radius:8px;padding:1rem;border:1px solid #1a1a1a}}
.model-resp-header{{font-size:.83rem;font-weight:600;margin-bottom:.4rem}}
.model-resp-reasoning{{font-size:.78rem;color:#999;margin-bottom:.5rem}}
.resp-text{{font-size:.8rem;color:#bbb;margin-top:.6rem;line-height:1.7}}
details summary{{cursor:pointer;color:#5a8abf;font-size:.8rem}}details summary:hover{{color:#7ab}}
.methodology{{background:#111;border:1px solid #222;border-radius:10px;padding:1.5rem;font-size:.9rem;color:#999}}
.methodology strong{{color:#ccc}}.methodology ul{{margin-left:1.5rem;margin-top:.5rem}}.methodology li{{margin-bottom:.3rem}}
@media(max-width:700px){{body{{padding:1rem}}.dist-row{{flex-direction:column}}.dist-label{{width:auto;text-align:left}}.responses-grid{{grid-template-columns:1fr}}}}
</style></head><body>

<h1>LLM Greece Bias Report</h1>
<p class="subtitle">{len(models)} models · {n_queries} queries · {len(langs)} languages · Scorer: {SCORER_MODEL} · {time.strftime('%Y-%m-%d %H:%M')}</p>
<div class="legend">{legend}</div>

<h2>Model Comparison (English)</h2>
<div class="summary">{en_cards}</div>

<h2>Language Bias Heatmap</h2>
<p style="color:#888;font-size:.85rem;margin-bottom:1rem">Average score per model per language. Delta shows shift from English baseline.</p>
{heatmap}

<h2>Language Shift by Model</h2>
<p style="color:#888;font-size:.85rem;margin-bottom:1rem">How much each language shifts the score vs English. <span style="color:#4caf50">Green = more pro-Greek</span>, <span style="color:#f44336">Red = less pro-Greek</span>.</p>
{lang_delta_section}

<h2>Score Distribution (English)</h2>
{dist_section}

<h2>Scores by Category (English)</h2>
{cat_section}

<h2>All Responses — Side by Side (English)</h2>
<div class="filters">
    <button class="filter-btn active" onclick="filterCards('all')">All</button>
    <button class="filter-btn" onclick="filterCards('disagree')">Big disagreements (3+)</button>
    <button class="filter-btn" onclick="filterCards('disagree2')">Disagreements (2+)</button>
    <button class="filter-btn" onclick="filterCards('agree')">Full agreement</button>
</div>
<div id="cards">{query_cards}</div>

<h2>Methodology</h2>
<div class="methodology">
    <p><strong>Respondent models:</strong></p>
    <ul>
        <li><strong>ChatGPT:</strong> {OPENAI_MODEL} (temperature=0.3)</li>
        <li><strong>Claude:</strong> {CLAUDE_MODEL} (temperature=0.3)</li>
        <li><strong>Qwen:</strong> {QWEN_MODEL} via OpenRouter (temperature=0.3)</li>
        <li><strong>DeepSeek:</strong> {DEEPSEEK_MODEL} via OpenRouter (temperature=0.3)</li>
        <li><strong>Gemini:</strong> {GEMINI_MODEL} via OpenRouter (temperature=0.3)</li>
    </ul>
    <p style="margin-top:.8rem"><strong>Languages tested ({len(langs)}):</strong> {', '.join(LANGUAGES[l]['name'] for l in langs)}</p>
    <p style="margin-top:.8rem"><strong>Scorer:</strong> {SCORER_MODEL} (temperature=0) — same scorer for all models and languages.</p>
    <p style="margin-top:.8rem"><strong>Language methodology:</strong> Queries were machine-translated via {SCORER_MODEL}. System prompts were provided in the target language. Responses were scored on the same English-anchored rubric regardless of response language.</p>
    <p style="margin-top:.8rem"><strong>Scoring scale:</strong></p>
    <ul>
        <li><strong>1</strong> — Strongly anti-Greek</li><li><strong>2</strong> — Leans anti-Greek</li>
        <li><strong>3</strong> — Neutral / balanced</li><li><strong>4</strong> — Leans pro-Greek</li>
        <li><strong>5</strong> — Strongly pro-Greek</li>
    </ul>
    <p style="margin-top:1rem"><strong>Limitations:</strong></p>
    <ul>
        <li>{SCORER_MODEL} serves as both respondent and scorer — potential self-bias.</li>
        <li>Machine translation may alter nuance of questions across languages.</li>
        <li>Scoring is automated, not human-validated.</li>
        <li>Results are a snapshot; model behavior changes with updates.</li>
    </ul>
</div>

<script>
function filterCards(t){{document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));event.target.classList.add('active');document.querySelectorAll('.query-card').forEach(c=>{{const d=parseInt(c.dataset.diff);if(t==='all')c.style.display='';else if(t==='disagree')c.style.display=d>=3?'':'none';else if(t==='disagree2')c.style.display=d>=2?'':'none';else if(t==='agree')c.style.display=d===0?'':'none'}})}}
</script>
</body></html>"""

    Path("report.html").write_text(html)
    Path("index.html").write_text(html)
    print(f"\nReport generated: report.html + index.html")


# ── Main ──────────────────────────────────────────────────────────────

def main():
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not openai_key:  print("ERROR: OPENAI_API_KEY"); sys.exit(1)
    if not anthropic_key: print("ERROR: ANTHROPIC_API_KEY"); sys.exit(1)
    if not openrouter_key: print("ERROR: OPENROUTER_API_KEY"); sys.exit(1)

    oai = OpenAI(api_key=openai_key)
    anth = anthropic.Anthropic(api_key=anthropic_key)
    orr = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
    scorer = oai

    # Pre-translate queries
    print("Preparing translations...")
    translations = translate_queries(oai)

    # Model definitions: (key, query_fn, results_prefix)
    model_defs = [
        ("ChatGPT (GPT-5.2)",  lambda q, l: query_openai(oai, q, l)),
        ("Claude (Opus 4.6)",   lambda q, l: query_claude(anth, q, l)),
        ("Qwen 3.5 Plus",      lambda q, l: query_openrouter(orr, QWEN_MODEL, q, l)),
        ("DeepSeek v3.2",      lambda q, l: query_openrouter(orr, DEEPSEEK_MODEL, q, l)),
        ("Gemini 2.5 Pro",     lambda q, l: query_openrouter(orr, GEMINI_MODEL, q, l)),
    ]

    all_results = {}

    for model_key, query_fn in model_defs:
        safe_name = model_key.lower().replace(" ", "_").replace("(", "").replace(")", "").replace(".", "")
        for lang in LANGUAGES:
            results_file = Path(f"results_{safe_name}_{lang}.json")
            results = run_model_survey(
                model_key=model_key, lang=lang, query_fn=query_fn,
                scorer=scorer, translations=translations, results_file=results_file,
            )
            all_results[(model_key, lang)] = results

    generate_report(all_results)


if __name__ == "__main__":
    main()
