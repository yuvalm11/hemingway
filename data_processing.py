import re
import json
from pathlib import Path
from typing import List


def clean_text(text: str) -> str:
    pg_start_markers = [
        r'^\s*Updated editions will replace',
        r'^\s*START: FULL LICENSE',
        r'^\s*PLEASE READ THIS BEFORE YOU DISTRIBUTE',
        r'^\s*End of.*Project Gutenberg',
        r'^\s*End of the Project Gutenberg'
    ]
    
    lines = text.split('\n')
    content_end_idx = len(lines)
    
    for i, line in enumerate(lines):
        if any(re.search(marker, line, re.IGNORECASE) for marker in pg_start_markers):
            content_end_idx = i
            break
    
    text = '\n'.join(lines[:content_end_idx])
    
    lines = text.split('\n')
    cleaned_lines = []
    
    in_content = False
    skip_patterns = [
        r'^.*produced by.*$',
        r'^.*project gutenberg.*$',
        r'^.*etext.*$',
        r'^.*charles scribner.*$',
        r'^.*copyright.*$',
        r'^.*all rights reserved.*$',
        r'^.*printed in.*$',
        r'^this book is for.*$',
        r'^.*book is for.*$',
        r'^\s*to\s+$',
        r'^\s*dedicated.*$',
        r'^.*transcriber.*$',
        r'^\s*of \d+ copies.*$',
        r'^\s*\d{4}\s*$',
        r'^\s*\d{4}\.',
        r'^project gutenberg',
        r'^.*electronic.*',
        r'^.*distribution.*license.*'
    ]
    
    for line in lines:
        if re.search(r'project gutenberg', line, re.IGNORECASE):
            continue
        if re.search(r'please read this before you distribute', line, re.IGNORECASE):
            break
            
        if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
            continue
            
        if not in_content:
            if re.match(r'^\s*(CHAPTER|BOOK|chapter|book)\s+\d+', line, re.IGNORECASE):
                in_content = True
                continue
            elif len(line.strip()) > 30 and re.search(r'[a-z]', line):
                in_content = True
        
        if in_content:
            cleaned_lines.append(line)
    
    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    paragraphs = cleaned_text.split('\n\n')
    filtered_paragraphs = []
    
    for para in paragraphs:
        if len(para.strip()) < 3:
            continue
            
        if re.match(r'^.*book is for\s+[A-Z]', para, re.IGNORECASE):
            continue
        if re.match(r'^["""].*generation.*["""]', para, re.IGNORECASE):
            continue
        if re.match(r'^.*lost generation.*', para, re.IGNORECASE):
            continue
        if re.search(r'(Ecclesiastes|GERTRUDE STEIN.*conversation)', para, re.IGNORECASE):
            continue
        if re.match(r'^—', para):
            continue
        if re.match(r'^.*in conversation$', para, re.IGNORECASE):
            continue
        if re.search(r'may be reproduced in any form', para, re.IGNORECASE):
            continue
        if len(para) < 50 and para.isupper() and not re.search(r'[.!?]$', para):
            continue
        if para.count('_') > len(para) // 3:
            continue
        if re.search(r'project gutenberg|license|intellectual property|copyright.*project', para, re.IGNORECASE):
            if len(para) > 200:
                continue
        if any(word in para.lower() for word in ['royalties', 'fees', 'electronic works', 'distribution', 'www.gutenberg.org']):
            if len(para) > 100:
                continue
        filtered_paragraphs.append(para)
    
    cleaned_text = '\n\n'.join(filtered_paragraphs)
    
    return cleaned_text.strip()


def split_into_chunks(text: str, min_tokens: int = 64, max_tokens: int = 1024) -> List[str]:
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        para_tokens = len(para) // 4
        
        if para_tokens > max_tokens:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            sentences = re.split(r'(?<=[.!?])\s+', para)
            sentence_para = ''
            for sentence in sentences:
                if (len(sentence_para) + len(sentence) + 1) // 4 > max_tokens:
                    if sentence_para:
                        chunks.append(sentence_para.strip())
                    sentence_para = sentence
                else:
                    if sentence_para:
                        sentence_para += ' ' + sentence
                    else:
                        sentence_para = sentence
            
            if sentence_para:
                current_chunk = [sentence_para.strip()]
                current_size = len(sentence_para) // 4
            continue
        
        if current_size + para_tokens > max_tokens and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_tokens
            continue
        
        current_chunk.append(para)
        current_size += para_tokens
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    chunks = [chunk for chunk in chunks if len(chunk) // 4 >= min_tokens]
    
    return chunks


def process_file(filepath: Path) -> List[dict]:
    """Process a single file and return list of text chunks."""
    print(f"Processing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    cleaned = clean_text(raw_text)
    chunks = split_into_chunks(cleaned)
    formatted_chunks = [{"text": chunk} for chunk in chunks]
    
    print(f"  Generated {len(formatted_chunks)} chunks from {filepath.name}")
    return formatted_chunks


def main():
    output_dir = Path('training_data')
    output_dir.mkdir(exist_ok=True)
    
    data_dir = Path('data')
    text_files = sorted(data_dir.glob('*.txt'))
    
    if not text_files:
        print("No text files found in data directory!")
        return
    
    print(f"Found {len(text_files)} text files to process\n")
    
    all_chunks = []
    
    for filepath in text_files:
        try:
            chunks = process_file(filepath)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error processing {filepath.name}: {e}")
            continue
    
    output_file = output_dir / 'hemingway_training_data.jsonl'
    with open(output_file, 'w', encoding='utf-8') as f:
        for chunk in all_chunks:
            json.dump(chunk, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"\n✓ Processed {len(all_chunks)} total chunks")
    print(f"✓ Saved to {output_file}")


if __name__ == '__main__':
    main()

