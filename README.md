# Dataset Enhancer with OpenAI Compatible API 🚀

A powerful CLI tool to enhance your dataset using any OpenAI compatible API. This tool extracts key points from web articles and adds them to your dataset in a structured format.

## Features ✨

- 🎯 Interactive menu interface
- 🌐 Interactive URL input with validation
- 💾 Automatic dataset backup
- 🔑 Secure API key management
- 📊 Beautiful progress indicators
- 📋 Dataset validation
- 🎨 Rich, colorful interface
- 🔄 Interactive mode
- 🔌 Works with any OpenAI compatible API
- 📝 ShareGPT format conversion for fine-tuning
- ✅ Fact-checking of key points using Ollama's Bespoke-MiniCheck model

## Installation 🛠️

1. Clone the repository:

```bash
git clone https://github.com/ncls-p/llm-to-blog-key-points-dataset.git
cd pplx-to-dataset
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your environment:

```bash
cp .env.example .env
```

4. Edit `.env` and add your API configuration:

```
OPENAI_COMPATIBLE_API_KEY=your-api-key-here
OPENAI_COMPATIBLE_API_URL=https://api.openai.com
OPENAI_COMPATIBLE_MODEL=gpt-3.5-turbo
```

## Usage 📚

### Interactive Menu

Simply run:

```bash
python cli.py
```

This will open the interactive menu with the following options:

- 🌐 Process URLs: Add new articles to your dataset
- 🧹 Clean Existing Dataset: Clean references from dataset entries
- 📊 View Dataset Info: See statistics about your dataset
- ✅ Validate Dataset: Check for any invalid entries
- 🔄 Convert to ShareGPT Format: Convert dataset to ShareGPT format for fine-tuning
- 🔑 Manage API Key: View, update, or remove your API key
- ❌ Exit: Close the application

### Command Line Mode

You can also use command-line arguments:

Process URLs:

```bash
python cli.py process --dataset "my_dataset.json" --no-backup
```

Validate dataset:

```bash
python cli.py validate "my_dataset.json"
```

Convert to ShareGPT format:

```bash
python cli.py convert-to-sharegpt "my_dataset.json" "my_dataset_sharegpt.json"
```

## Features in Detail 🔍

### API Key Management 🔑

- View current API key (safely masked)
- Update API key
- Remove API key
- Automatic .env file handling

### Dataset Processing 🌐

- Interactive URL input
- URL format validation
- Multiple URL support
- Progress tracking
- Automatic backup

### Dataset Information 📊

- Total entries count
- File size
- Last modified date
- Validation status

## Dataset Format 📝

### Standard Format

The tool maintains the following format for each entry:

```json
{
  "instruction": "",
  "input": "Full article content",
  "output": "Key points extracted by the AI"
}
```

### ShareGPT Format

You can convert your dataset to ShareGPT format for fine-tuning:

```json
{
  "conversations": [
    { "from": "human", "value": "Full article content" },
    { "from": "gpt", "value": "Key points extracted by the AI" }
  ],
  "source": "article-key-points"
}
```

This format is compatible with many fine-tuning tools and datasets like [FineTome-100k](https://huggingface.co/datasets/mlabonne/FineTome-100k).

## Environment Variables 🔐

- `OPENAI_COMPATIBLE_API_KEY`: Your API key
- `OPENAI_COMPATIBLE_API_URL`: Base URL for the API (e.g., https://api.openai.com)
- `OPENAI_COMPATIBLE_MODEL`: Model to use (e.g., gpt-3.5-turbo)
- `OLLAMA_API_URL`: URL for Ollama API (default: http://localhost:11434/v1/chat/completions)
- `FACT_CHECK_MODEL`: Model to use for fact-checking (default: bespoke-minicheck)
  - All can be set in `.env` file
  - API key can be managed through the interactive menu
  - Will prompt for input if not found
  - Option to save to `.env` when entered manually

## Fact-Checking Functionality ✅

The tool now includes the ability to verify the accuracy of extracted key points against the original content using Ollama's Bespoke-MiniCheck model.

### How It Works

1. Each key point is individually verified against the original article content
2. The fact-checking model classifies each point as:
   - ✅ **Consistent**: The key point is accurate and supported by the content
   - ❌ **Inconsistent**: The key point contains inaccuracies or is not supported by the content
   - ❓ **Uncertain**: The model cannot determine the accuracy with confidence

### Using Fact-Checking

When processing URLs:

```bash
python cli.py process --dataset "my_dataset.json" --verify-points
```

To verify an existing dataset:

```bash
python cli.py verify-dataset "my_dataset.json" "my_verified_dataset.json"
```

### Verification Results

The verification results are stored in the dataset as a new field:

```json
{
  "instruction": "",
  "input": "Full article content",
  "output": "Key points extracted by the AI",
  "verification_results": {
    "accurate": [
      {
        "point": "Point that was verified as accurate",
        "verification": {
          "is_accurate": true,
          "explanation": "Consistent: This point is supported by the document...",
          "raw_response": "Full response from the fact-checking model"
        }
      }
    ],
    "inaccurate": [...],
    "uncertain": [...]
  }
}
```

### Requirements

To use the fact-checking functionality, you need:

1. [Ollama](https://ollama.com/) installed and running locally (or accessible via network)
2. The [Bespoke-MiniCheck](https://ollama.com/library/bespoke-minicheck) model pulled into Ollama:
   ```bash
   ollama pull bespoke-minicheck
   ```

## Compatible APIs 🔌

This tool works with any API that follows the OpenAI chat completions format, including:

- OpenAI
- Perplexity AI
- Anthropic (with adapter)
- Azure OpenAI
- Local models (with compatible servers)

## Error Handling 🛡️

The tool includes comprehensive error handling for:

- Invalid URLs
- API failures
- Invalid dataset format
- Network issues
- Rate limiting

## Acknowledgments 🙏

- Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
