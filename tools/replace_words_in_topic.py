import json
import re

MAX_LENGTH = 35

# Word-level abbreviation dictionary
ABBREVIATIONS = {
    "introduction": "Intro",
    "accounting": "Acct",
    "disclosure": "Discl",
    "as": "as",
    "cash": "Cash",
    "financial": "Fin",
    "recognition": "Recogn",
    "statements": "Stmts",
    "measurement": "Meas",
    "standards": "Stds",
    "definitions": "Defs",
    "amalgamation": "Amalg",
    "assets": "Asts",
    "from": "Frm",
    "loss": "Loss",
    "standard": "Std",
    "scope": "Scp",
    "or": "or",
    "cost": "Cost",
    "foreign": "For",
    "flows": "Flws",
    "disclosures": "Discls",
    "terms": "Trms",
    "used": "Used",
    "treatment": "Treat",
    "other": "Oth",
    "costs": "Costs",
    "benefits": "Ben",
    "impairment": "Imp",
    "grants": "Grts",
    "company": "Co",
    "reporting": "Reptg",
    "exchange": "Exch",
    "related": "Rel",
    "presentation": "Pres",
    "revenue": "Rev",
    "asset": "Ast",
    "amount": "Amt",
    "books": "Bks",
    "method": "Mtd",
    "consolidated": "Consol",
    "policies": "Pols",
    "meaning": "Mean",
    "definition": "Defn",
    "share": "Shr",
    "interim": "Intm",
    "estimates": "Ests",
    "non": "Non",
    "investments": "Invs",
    "government": "Govt",
    "and": "&"
}


# Optional phrase-level replacements first, before word replacements
PHRASE_REPLACEMENTS = {
    "head office": "HO",
    "Accounting Standards": "AS",
    "accounting standards": "AS",
    "branch and head office": "Branch & HO",
    "branch& head office": "Branch & HO",
    "adjustment and reconciliation": "Adj & Recon",
    "methods of": "Methods of",
    "accounting for": "Acc for",
    "incorporation of": "Incorp of",
    "balance in": "Bal in"
}

STOPWORDS = {"of", "the", "for", "to", "in", "on", "at", "by", "with", "a", "an"}


def normalize_spaces(text):
    text = re.sub(r"\s*&\s*", " & ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def apply_phrase_replacements(text):
    result = text
    for phrase, replacement in PHRASE_REPLACEMENTS.items():
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
        result = pattern.sub(replacement, result)
    return result


def apply_word_abbreviations(text):
    words = text.split()
    new_words = []

    for word in words:
        # Separate punctuation from word
        match = re.match(r"^([A-Za-z&]+)([^A-Za-z&]*)$", word)
        if match:
            core = match.group(1)
            punct = match.group(2)
            short_core = ABBREVIATIONS.get(core.lower(), core)
            new_words.append(short_core + punct)
        else:
            new_words.append(word)

    return " ".join(new_words)


def remove_stopwords_if_needed(text, max_length=MAX_LENGTH):
    if len(text) <= max_length:
        return text

    words = text.split()
    filtered = [w for w in words if w.lower() not in STOPWORDS]

    if filtered:
        return " ".join(filtered)
    return text


def aggressive_shorten(text, max_length=MAX_LENGTH):
    """
    Final fallback if still too long:
    - Shorten long words to first 4 chars + '.'
    - Keep short words as they are
    """
    if len(text) <= max_length:
        return text

    words = text.split()
    shortened = []

    for w in words:
        clean = re.sub(r"[^A-Za-z&]", "", w)
        if len(clean) > 6:
            short = clean[:4] + "."
            punct = w[len(clean):] if w.startswith(clean) else ""
            shortened.append(short + punct)
        else:
            shortened.append(w)

    result = " ".join(shortened)

    if len(result) <= max_length:
        return result

    return result[:max_length].rstrip()


def create_short_topic_name(topic_name, max_length=MAX_LENGTH):
    topic_name = normalize_spaces(topic_name)

    if len(topic_name) <= max_length:
        return topic_name

    short_name = apply_phrase_replacements(topic_name)
    short_name = normalize_spaces(short_name)

    if len(short_name) <= max_length:
        return short_name

    short_name = apply_word_abbreviations(short_name)
    short_name = normalize_spaces(short_name)

    if len(short_name) <= max_length:
        return short_name

    short_name = remove_stopwords_if_needed(short_name, max_length)
    short_name = normalize_spaces(short_name)

    if len(short_name) <= max_length:
        return short_name

    short_name = aggressive_shorten(short_name, max_length)
    return short_name


def update_topic_names(obj):
    if isinstance(obj, list):
        for item in obj:
            update_topic_names(item)

    elif isinstance(obj, dict):
        if "topic_name" in obj and isinstance(obj["topic_name"], str):
            obj["topic_name_abbvtd"] = create_short_topic_name(obj["topic_name"])

        for value in obj.values():
            update_topic_names(value)


def process_json_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    update_topic_names(data)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Processed file saved to: {output_file}")


if __name__ == "__main__":
    input_file = r"H:\Other computers\Office_Desktop\EffCorp_Projects\cap-online\books\concept-book\syllabus-engine\data\1-ca-inter-adv-accounts-topic-page-index.json"
    output_file = r"H:\Other computers\Office_Desktop\EffCorp_Projects\cap-online\books\concept-book\syllabus-engine\data\1-ca-inter-adv-accounts-topic-page-index_shortened.json"
    process_json_file(input_file, output_file)
