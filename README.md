# Hemingway LLM

Fine tuning of TinyLlama on Hemingway's work to generate Hemingway-like text.
Hemingway is one of the most famous authors of the 20th century, and his style is characterized by its simplicity, directness, and clarity.
This project aims to fine tune a TinyLlama model to generate text that is similar to Hemingway's style.

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Process the data (if not already done):
```bash
python data_processing.py
```

4. Train the model:
```bash
python train.py
```

## Data

There are a few public domain books by Hemingway I gathered from Project Gutenberg. These include:
- A Farewell to Arms
- The Sun Also Rises
- Men Without Women
- In Our Time
- Three Stories & Ten Poems

The plain text files were then cleaned up to remove headers, footers, and other metadata and formatted into a collection of paragraphs that can be used as training data for the model.

