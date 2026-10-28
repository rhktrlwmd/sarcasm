# Manual Russian Conversational Sarcasm Dataset

This file was manually curated from publicly visible Reddit snippets and discussion pages, primarily from:

- `r/Pikabu`
- `r/rusAskReddit`

The file now also includes a larger block of **manual authored and manual generated conversational examples** marked with:

- `source_url = manual://authored`
- `source_type = manual_authored`
- `source_url = manual://generated`
- `source_type = manual_generated`

## Intended use

- Improve Russian sarcasm detection for conversational text
- Reduce dependence on satirical news headlines
- Provide a cleaner `sarcastic` vs `not_sarcastic` split for short user-style utterances

## Label policy

- `1` = sarcastic conversational speech
- `0` = ordinary non-sarcastic speech

Excluded on purpose:

- pure jokes
- fantasy satire headlines
- generic irony without clear conversational intent

## Columns

- `text`
- `label`
- `source_url`
- `source_type`
- `curation_note`

## Important limitation

This is a **manually curated and manually expanded training supplement**, not a benchmark scraped from one platform. Some examples were taken from publicly visible Reddit snippets, some were manually authored, and some were generated from controlled conversational templates to cover recurring sarcasm patterns such as exaggerated praise, queue complaints, sarcastic gratitude, deadline frustration, and sincere non-sarcastic speech with occasional emphasis. Treat the corpus as a Russian-domain adaptation set for course work experiments rather than a final standalone benchmark.
