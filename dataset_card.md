---
language:
  - en
pretty_name: "Article Key Points Dataset"
tags:
  - text
  - summarization
  - perplexity-ai
  - article-extraction
license: "cc-by-4.0"
task_categories:
  - summarization
  - text-generation
size_categories:
  - n<1K
---

# Article Key Points Dataset

## Dataset Description

This dataset contains articles and their corresponding key points extracted using Perplexity AI. Each entry consists of the full article text and a concise bullet-point summary highlighting the most important information from the article.

### Dataset Summary

The dataset is designed for training and evaluating models on extractive and abstractive summarization tasks. It provides pairs of full article content and human-readable key point summaries that capture the essential information from each article.

## Dataset Structure

### Data Instances

Each instance in the dataset contains:

```json
{
  "instruction": "Full article content",
  "input": "",
  "output": "Here are the key points of the article:\n* Key point 1\n* Key point 2\n* Key point 3\n..."
}
```

### Data Fields

- `instruction`: The full text of the article
- `input`: Empty field (reserved for potential future use)
- `output`: A bullet-point list of key points extracted from the article

### Data Splits

The dataset is provided as a single collection without predefined splits.

## Dataset Creation

### Curation Rationale

This dataset was created to provide high-quality article-summary pairs for training summarization models. The key points are focused on extracting the most important information from each article in a concise format.

### Source Data

#### Initial Data Collection and Normalization

Articles were collected from various online sources. The full text of each article was preserved in its original form.

#### Who are the source data producers?

The source data comes from publicly available articles from various online publications.

### Annotations

#### Annotation process

The key points were automatically extracted using Perplexity AI's API. The extraction process focused on identifying the most important information from each article and presenting it in a concise, bullet-point format.

#### Who are the annotators?

The annotations (key points) were generated using [Perplexity AI](https://docs.perplexity.ai/), a large language model service. The extraction was performed using a custom tool called [Dataset Enhancer](https://github.com/ncls-p/pplx-to-dataset), which processes articles and extracts key points using the Perplexity API.

### Personal and Sensitive Information

Care was taken to avoid including personal or sensitive information in the dataset. However, as the dataset contains content from public articles, it may include names of public figures or information that was already in the public domain.

## Considerations for Using the Dataset

### Social Impact of Dataset

This dataset aims to improve summarization capabilities of language models, which can help users quickly understand the key points of long articles, saving time and improving information accessibility.

### Discussion of Biases

The dataset may contain biases present in the source articles or introduced during the key point extraction process. Users should be aware that:

1. The selection of articles may not represent all perspectives equally
2. The automated extraction of key points may emphasize certain types of information over others
3. The language model used for extraction may have its own inherent biases

### Dataset Curators

This dataset was curated using the [Dataset Enhancer](https://github.com/ncls-p/pplx-to-dataset) tool, which was created to automate the process of extracting key points from articles using Perplexity AI.

### Licensing Information

This dataset is released under the [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) license.

### Citation Information

If you use this dataset in your research, please cite:

```
@misc{article-key-points-dataset,
  author = {Your Name},
  title = {Article Key Points Dataset},
  year = {2023},
  howpublished = {Hugging Face Dataset},
  url = {https://huggingface.co/datasets/your-username/article-key-points}
}
```

### Contributions

Thanks to [Perplexity AI](https://docs.perplexity.ai/) for providing the API used to generate the key points and to the [Dataset Enhancer](https://github.com/ncls-p/pplx-to-dataset) tool for automating the dataset creation process.
