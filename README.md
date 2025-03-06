# LLM Key Points Dataset Generator

A tool for generating and managing datasets of key points extracted from web content using OpenAI-compatible APIs, with verification capabilities.

## Features

- Extract key points from web articles using any OpenAI-compatible API
- Clean up references and citations from extracted content
- Verify key points against original content using Bespoke-MiniCheck via Ollama
- Convert datasets to ShareGPT format for fine-tuning
- Interactive CLI with rich text formatting

## Installation

### Option 1: Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/llm-to-blog-key-points-dataset.git
cd llm-to-blog-key-points-dataset

# Install the package
pip install -e .
```

### Option 2: Install dependencies only

```bash
pip install -r requirements.txt
```

## Usage

### As a command-line tool

After installation, you can run the tool directly from the command line:

```bash
# Launch the interactive menu
llm-key-points

# Or use specific commands
llm-key-points process --dataset ./my_dataset.json
```

### Running from source

You can also run the tool directly from the source code:

```bash
# Using the interactive menu
python main.py

# Using direct commands
python -m llm_key_points.interfaces.cli process --dataset ./my_dataset.json
```

## Commands

- `process`: Process URLs and extract key points
- `clean`: Clean references from existing dataset entries
- `verify`: Verify key points against original content
- `validate`: Check dataset for validity
- `convert`: Convert dataset to ShareGPT format

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Required
OPENAI_COMPATIBLE_API_KEY=your_api_key_here

# Optional
OPENAI_COMPATIBLE_API_URL=https://api.openai.com
OPENAI_COMPATIBLE_MODEL=gpt-3.5-turbo
OLLAMA_API_URL=http://localhost:11434/v1/chat/completions
FACT_CHECK_MODEL=bespoke-minicheck
```

## Project Structure (Clean Architecture)

The project follows clean architecture principles with clearly separated layers:

```
llm_key_points/
├── core/                  # Core business logic
│   ├── entities/          # Business entities
│   ├── interfaces/        # Abstract interfaces
│   └── use_cases/         # Application business rules
├── adapters/              # Interface adapters
│   ├── api/               # API clients
│   ├── repositories/      # Data storage implementations
│   ├── verification/      # Verification service implementations
│   └── web/               # Web content handling
└── interfaces/            # External interfaces
    ├── cli/               # Command-line interface
    └── console/           # Console output formatting
```

### Key Components

- **Core Domain Layer**: Contains business entities and logic isolated from external dependencies
- **Use Cases**: Orchestration of business logic flows
- **Interfaces**: Abstract contracts that define how layers interact
- **Adapters**: Concrete implementations of interfaces that connect to external services
- **UI Layer**: User interface implementations (CLI in this case)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

Created with ❤️ by Ncls-p
