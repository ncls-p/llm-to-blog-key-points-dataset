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
- 📊 View Dataset Info: See statistics about your dataset
- ✅ Validate Dataset: Check for any invalid entries
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

The tool maintains the following format for each entry:

```json
{
  "instruction": "",
  "input": "Full article content",
  "output": "Key points extracted by the AI"
}
```

## Environment Variables 🔐

- `OPENAI_COMPATIBLE_API_KEY`: Your API key
- `OPENAI_COMPATIBLE_API_URL`: Base URL for the API (e.g., https://api.openai.com)
- `OPENAI_COMPATIBLE_MODEL`: Model to use (e.g., gpt-3.5-turbo)
  - All can be set in `.env` file
  - API key can be managed through the interactive menu
  - Will prompt for input if not found
  - Option to save to `.env` when entered manually

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
