from pathlib import Path
import re
import sys
import time
from deep_translator import GoogleTranslator

sys.stdout.reconfigure(encoding='utf-8')

INPUT_PATH = Path('book/chapter0.md')
OUTPUT_PATH = Path('book/chapter0_hindi.md')


def translate_with_retry(text, max_retries=3):
    """Translate text with exponential backoff retry logic."""
    translator = GoogleTranslator(source='auto', target='hi')
    for attempt in range(max_retries):
        try:
            result = translator.translate(text)
            if result is not None and result.strip():
                return result
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s
    return None


def chunk_text(text: str, max_chars: int = 1500):
    """Split text into smaller, safer chunks."""
    # Split by sentences first for better semantic chunks
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ''

    for sentence in sentences:
        if len(current) + len(sentence) + 1 > max_chars:
            if current.strip():
                chunks.append(current.strip())
            current = sentence
        else:
            current += ' ' + sentence if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


if __name__ == '__main__':
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    source_text = INPUT_PATH.read_text(encoding='utf-8')
    
    # First pass: identify paragraph boundaries
    paragraphs = re.split(r'\n\s*\n', source_text)
    translated_paragraphs = []

    total = len(paragraphs)
    for para_idx, para in enumerate(paragraphs, 1):
        if not para.strip():
            translated_paragraphs.append('\n\n')
            continue

        # Break each paragraph into sentences
        chunks = chunk_text(para)
        translated_chunks = []

        for chunk_idx, chunk in enumerate(chunks, 1):
            print(f"Para {para_idx}/{total}, Chunk {chunk_idx}/{len(chunks)}...", end=' ', flush=True)
            translated = translate_with_retry(chunk)
            
            if translated:
                translated_chunks.append(translated)
                print("✓")
            else:
                print("⚠ (kept original)")
                translated_chunks.append(chunk)

        translated_paragraphs.append(' '.join(translated_chunks))

    result = '\n\n'.join(translated_paragraphs)
    OUTPUT_PATH.write_text(result, encoding='utf-8')
    print(f'\n✓ Translated file written to: {OUTPUT_PATH.resolve()}')
    print(f'  File size: {OUTPUT_PATH.stat().st_size} bytes')

