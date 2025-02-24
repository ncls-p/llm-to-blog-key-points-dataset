# Dataset Enhancer with Perplexity AI 🚀

A powerful CLI tool to enhance your dataset using Perplexity AI's API. This tool extracts key points from web articles and adds them to your dataset in a structured format.

## Features ✨

- 🎯 Interactive menu interface
- 🌐 Interactive URL input with validation
- 💾 Automatic dataset backup
- 🔑 Secure API key management
- 📊 Beautiful progress indicators
- 📋 Dataset validation
- 🎨 Rich, colorful interface
- 🔄 Interactive mode

## Installation 🛠️

1. Clone the repository:

```bash
git clone https://github.com/ncls-p/pplx-to-dataset.git
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

4. Edit `.env` and add your Perplexity API key:

```
PERPLEXITY_API_KEY=pplx-your-api-key-here
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
  "instruction": "Full article content",
  "input": "",
  "output": "Key points extracted by Perplexity AI"
}
```

## Environment Variables 🔐

- `PERPLEXITY_API_KEY`: Your Perplexity AI API key
  - Can be set in `.env` file
  - Can be managed through the interactive menu
  - Will prompt for input if not found
  - Option to save to `.env` when entered manually

## Error Handling 🛡️

The tool includes comprehensive error handling for:

- Invalid URLs
- API failures
- Invalid dataset format
- Network issues
- Rate limiting

## Acknowledgments 🙏

- Powered by [Perplexity AI](https://docs.perplexity.ai/)
- Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)
