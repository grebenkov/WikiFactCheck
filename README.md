# WikiFactCheck

WikiFactCheck is a **PROOF OF CONCEPT** Python tool that fact-checks article text against source materials using OpenAI's language models API. It analyzes each word in the article and assigns a probability score indicating how well the word is supported by the source documents.

## Features

- Split articles into manageable blocks for processing
- Analyze each word against multiple source documents
- Color-code article text based on verification confidence:
  - **Green**: High confidence (>70% probability)
  - **Yellow**: Medium confidence (35-70% probability)
  - **Red**: Low confidence (<35% probability)
- Detailed JSON output of word-level verification

## Installation

```bash
# Clone the repository
git clone https://github.com/grebenkov/wikifactcheck.git
cd wikifactcheck

# Install dependencies
pip install -r openai colorama
```

## Requirements

- Python 3.7+
- OpenAI API key
- Required Python packages:
  - openai
  - colorama

## Usage

1. Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

2. Prepare your files:
   - Create an `article.txt` file with the article text you want to verify
   - Create one or more source files named `source1.txt`, `source2.txt`, etc.

3. Run the script:

```bash
python wikifactcheck.py
```

### Command-line Options

- `--base_url`: Base URL for OpenAI API (optional, for using alternative API endpoints)
- `--model`: OpenAI model to use (default: gpt-4.1-nano)

Example:
```bash
python wikifactcheck.py --model gpt-4-turbo
```

## How It Works

1. The program loads the article text and all source documents.
2. It splits the article into ~100-word blocks of complete sentences.
3. For each block, it queries the OpenAI model to compare the text against each source.
4. The model assigns a probability score (0.0 to 1.0) to each word, indicating how well it's supported.
5. The program combines the results and color-codes the article text based on verification confidence.

## Output

The program outputs a color-coded version of the article text in the terminal:
- **Green**: Words with strong support from sources
- **Yellow**: Words with moderate support
- **Red**: Words with little to no support

## Examples

![Screenshot 2025-05-04 232813](https://github.com/user-attachments/assets/13862ed2-0b1a-4253-b721-10aab44d4ab3)

![Screenshot 2025-05-04 233055](https://github.com/user-attachments/assets/9688a883-ad7c-44f6-9c56-558c701d6e3e)

## Limitations

- Accuracy depends on the quality and completeness of source materials
- API rate limits may affect processing time for large articles
- The tool provides a best-effort assessment and should not replace human review

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the BSD 3-clause License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the API
- The colorama library for terminal coloring capabilities
