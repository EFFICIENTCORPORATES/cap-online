import json
import re
from collections import Counter

json_file = r"H:\Other computers\Office_Desktop\EffCorp_Projects\cap-online\books\concept-book\syllabus-engine\data\1-ca-inter-adv-accounts-topic-page-index.json"

stop_words = {
    "the", "and", "of", "for", "to", "in", "on", "at", "by", "with",
    "a", "an", "&"
}

word_counter = Counter()


def extract_topic_names(obj):
    topic_names = []

    if isinstance(obj, list):
        for item in obj:
            topic_names.extend(extract_topic_names(item))

    elif isinstance(obj, dict):
        if "topic_name" in obj and isinstance(obj["topic_name"], str):
            topic_names.append(obj["topic_name"])

        for value in obj.values():
            topic_names.extend(extract_topic_names(value))

    return topic_names


with open(json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

topic_names = extract_topic_names(data)

for topic_name in topic_names:
    words = re.findall(r"[A-Za-z]+", topic_name.lower())
    filtered_words = [word for word in words if word not in stop_words]
    word_counter.update(filtered_words)

print(f"Total topic names found: {len(topic_names)}")
print("\nTop 50 repeated words in topic_name:\n")

for word, count in word_counter.most_common(50):
    print(f"{word}: {count}")
