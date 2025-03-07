# Changelog

## [Unreleased]

### Added

- Automatic verification of key points using Bespoke-MiniCheck right after generation
- Automatic regeneration of key points when inaccuracies are detected
- Integration of fact checker with key points extractor for improved accuracy
- New CLI options for configuring auto-check behavior:
  - `--auto-check/-a` flag to enable automatic verification
  - `--max-attempts/-m` option to set maximum regeneration attempts
- ExtractorConfig class for handling extraction configuration
- Improved error handling and logging for verification attempts

### Changed

- ExtractKeyPointsUseCase now injects fact checker into extractor for seamless verification
- Improved logging of key point regeneration attempts
- ExtractKeyPointsUseCase now accepts auto-check configuration
- OpenAICompatibleExtractor refactored to support configurable verification
- CLI interface updated to expose verification options to users

## [0.1.0] - 2024-03-13

### Added

- Initial release with core functionality
- Extract key points from web content using OpenAI-compatible APIs
- Verify key points against original content using Ollama/Bespoke-MiniCheck
- Clean up references and citations from extracted content
- Convert datasets to ShareGPT format for fine-tuning
- Interactive CLI with rich text formatting
- Save and load datasets in JSON format with automatic backups
- Web content extraction with BeautifulSoup
- Progress tracking and statistics reporting
- Clean architecture implementation with separated concerns
- Comprehensive test suite with pytest
- Environment variable configuration support
