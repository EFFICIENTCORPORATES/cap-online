from __future__ import annotations
import re
from collections import defaultdict
from .models import Block, QuerySpec

QUESTION_TYPES = {
    "tyk_mcq_question", "tyk_true_false_question", "tyk_theory_question",
    "tyk_practical_question", "tyk_scenario_question",
    "illustration_question", "example_question",
}
ANSWER_TYPES = {
    "answer_mcq", "answer_true_false", "answer_theory", "answer_practical",
    "answer_scenario", "illustration_solution", "example_solution",
}
PAIR_TO_ANSWER = {
    "tyk_mcq_question": "answer_mcq",
    "tyk_true_false_question": "answer_true_false",
    "tyk_theory_question": "answer_theory",
    "tyk_practical_question": "answer_practical",
    "tyk_scenario_question": "answer_scenario",
    "illustration_question": "illustration_solution",
    "example_question": "example_solution",
}

PRESETS = {
    "mcq": ({"tyk_mcq_question"}, False, "All MCQs"),
    "mcq_with_answers": ({"tyk_mcq_question"}, True, "MCQs with Answers"),
    "theory": ({"tyk_theory_question"}, False, "Theoretical Questions"),
    "theory_with_answers": ({"tyk_theory_question"}, True, "Theoretical Questions with Answers"),
    "practical": ({"tyk_practical_question"}, False, "Practical Questions"),
    "practical_with_answers": ({"tyk_practical_question"}, True, "Practical Questions with Answers"),
    "true_false": ({"tyk_true_false_question"}, False, "True/False Questions"),
    "true_false_with_answers": ({"tyk_true_false_question"}, True, "True/False Questions with Answers"),
    "scenario": ({"tyk_scenario_question"}, False, "Scenario-Based Questions"),
    "scenario_with_answers": ({"tyk_scenario_question"}, True, "Scenario-Based Questions with Answers"),
    "illustration_questions": ({"illustration_question"}, False, "Illustration Questions Only"),
    "illustrations": ({"illustration_question"}, True, "Illustrations with Solutions"),
    "example_questions": ({"example_question"}, False, "Safely Separable Example Questions Only"),
    "examples": ({"example"}, False, "All Source Examples"),
    "all_questions": (QUESTION_TYPES, False, "All Questions"),
    "all_questions_with_answers": (QUESTION_TYPES, True, "All Questions with Available Answers"),
    "topics": ({"topic"}, False, "Topics"),
    "summaries": ({"summary"}, False, "Summaries"),
    "learning_outcomes": ({"learning_outcomes"}, False, "Learning Outcomes"),
}


def spec_from_preset(name: str) -> QuerySpec:
    if name == "everything":
        return QuerySpec(everything=True, title="All Content")
    if name not in PRESETS:
        raise KeyError(f"Unknown preset: {name}")
    types, include_answers, title = PRESETS[name]
    return QuerySpec(types=set(types), include_answers=include_answers, title=title)


def parse_natural_query(text: str) -> QuerySpec:
    q = " ".join(text.strip().lower().split())
    if not q:
        return QuerySpec(everything=True, title="All Content", original_query=text)

    include_answers = any(x in q for x in ["with answer", "with solution", "and answer", "and solution", "including answer", "including solution"])
    no_answers = any(x in q for x in ["without answer", "without solution", "questions only", "question only", "only illustration question", "only example question"])
    include_answers = include_answers and not no_answers

    if "everything" in q or "all content" in q:
        spec = QuerySpec(everything=True, title="All Content", original_query=text)
    elif "illustration" in q:
        if "question" in q and ("only" in q or no_answers):
            spec = spec_from_preset("illustration_questions")
        else:
            spec = spec_from_preset("illustrations")
        if no_answers:
            spec.include_answers = False
    elif "example" in q:
        if "question" in q and ("only" in q or no_answers):
            spec = spec_from_preset("example_questions")
        else:
            spec = spec_from_preset("examples")
        if no_answers:
            spec.include_answers = False
    elif "mcq" in q or "multiple choice" in q:
        spec = spec_from_preset("mcq_with_answers" if include_answers else "mcq")
    elif "true false" in q or "true/false" in q:
        spec = spec_from_preset("true_false_with_answers" if include_answers else "true_false")
    elif "scenario" in q or "sbq" in q:
        spec = spec_from_preset("scenario_with_answers" if include_answers else "scenario")
    elif "theory" in q or "theoretical" in q:
        spec = spec_from_preset("theory_with_answers" if include_answers else "theory")
    elif "practical" in q:
        spec = spec_from_preset("practical_with_answers" if include_answers else "practical")
    elif "all question" in q or ("questions" in q and "all" in q):
        spec = spec_from_preset("all_questions_with_answers" if include_answers else "all_questions")
    elif "summary" in q or "summaries" in q:
        spec = spec_from_preset("summaries")
    elif "learning outcome" in q or "objective" in q:
        spec = spec_from_preset("learning_outcomes")
    elif "topic" in q:
        spec = spec_from_preset("topics")
    else:
        # Conservative: unknown intent means all content constrained by any hierarchy filters.
        spec = QuerySpec(everything=True, title="Filtered Content", original_query=text)

    spec.original_query = text
    spec.include_answers = spec.include_answers or include_answers
    spec.questions_only = no_answers

    for attr, patterns in {
        "paper": [r"\bpaper\s*(?:no\.?\s*)?(\d+)\b", r"\bp\s*0*(\d+)\b"],
        "module": [r"\bmodule\s*(\d+)\b", r"\bm\s*0*(\d+)\b"],
        "chapter": [r"\bchapter\s*(\d+)\b", r"\bc\s*0*(\d+)\b"],
        "unit": [r"\bunit\s*(\d+)\b", r"\bu\s*0*(\d+)\b"],
    }.items():
        for pat in patterns:
            m = re.search(pat, q, re.I)
            if m:
                setattr(spec, attr, int(m.group(1)))
                break
    tm = re.search(r"\btopic\s*([0-9]+(?:\.[0-9]+)*)\b", q, re.I)
    if tm:
        spec.topic = tm.group(1)
    return spec


def matches(block: Block, spec: QuerySpec) -> bool:
    if spec.paper is not None and block.paper != spec.paper:
        return False
    if spec.module is not None and block.module != spec.module:
        return False
    if spec.chapter is not None and block.chapter != spec.chapter:
        return False
    if spec.unit is not None and block.unit != spec.unit:
        return False
    if spec.topic and not (block.topic_number == spec.topic or block.topic_number.startswith(spec.topic + ".")):
        return False
    if spec.everything:
        # Full-content view uses one authoritative Example source item, not derivative Q/S views.
        return not bool(block.meta.get("registry_derivative"))
    if spec.types and block.type not in spec.types:
        return False
    if spec.categories and block.category not in spec.categories:
        return False
    return True


def select(blocks: list[Block], spec: QuerySpec) -> list[Block]:
    primary = [b for b in blocks if matches(b, spec)]
    if not spec.include_answers:
        return primary

    # pair_key values repeat across Units (for example illustration:1), so pairing
    # must be scoped to the same source Markdown document.
    by_pair: dict[tuple[str, str], list[Block]] = defaultdict(list)
    for b in blocks:
        if b.pair_key:
            by_pair[(str(b.document.path), b.pair_key)].append(b)

    selected_ids = set()
    out: list[Block] = []
    # Keep each selected question directly beside its available answer/solution.
    # This is a compilation view; provenance still points to the original source pages.
    for q in primary:
        if q.id not in selected_ids:
            out.append(q)
            selected_ids.add(q.id)
        if q.type not in QUESTION_TYPES or not q.pair_key:
            continue
        wanted = PAIR_TO_ANSWER.get(q.type)
        lookup_pair = str(q.meta.get("answer_ref_pair_key") or q.pair_key)
        shared_answer_ref = bool(q.meta.get("answer_ref_pair_key")) and lookup_pair != q.pair_key
        for candidate in by_pair.get((str(q.document.path), lookup_pair), []):
            if candidate.type == wanted and (candidate.id not in selected_ids or shared_answer_ref):
                out.append(candidate)
                if not shared_answer_ref:
                    selected_ids.add(candidate.id)
    return out
