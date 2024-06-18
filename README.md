Newslaunch is a Python package that provides a simple wrapper for interacting with the Guardian API and a utility for writing data to an AWS Kinesis stream. It also includes a CLI for querying the Guardian API.

## Installation

You can install Newslaunch via pip or pipx:

```bash
pip install newslaunch
pipx install newslaunch
```

## Usage

### Retrieve Articles from the Guardian and publish to AWS Kinesis

The example below shows how to use the GuardianAPI class to fetch articles from the Guardian and publish them to an AWS Kinesis stream using the KinesisWriter utility.

```python
from newslaunch import GuardianAPI
from newslaunch import KinesisWriter

# Initialize GuardianAPI with API key from environment
guardian_api = GuardianAPI()

# Initialize KinesisWriter with the stream name
kinesis_writer = KinesisWriter(stream_name="guardian_content")

# Retrieve articles
articles = guardian_api.search_articles("python programming", from_date="2023-01-01")

# Send articles to the Kinesis stream
response = kinesis_writer.send_to_stream(articles, record_per_entry=True)
```

### Command Line Interface (CLI)

Newslaunch also provides a CLI to interact with the Guardian API. You can set your API key and search for articles using simple commands.

```bash
newslaunch set-key --guardian <API_KEY>
newslaunch guardian "search_term"
```

## Documentation

For more detailed documentation on each component and available options, please refer to the [docs directory](docs/):

- [Guardian API Wrapper](docs/guardian_api.md)
- [AWS Kinesis Writer](docs/kinesis_writer.md)
- [CLI documentation](docs/cli.md).

## Development

1. Clone the repository:

   ```bash
   git clone https://github.com/pavzari/newslaunch.git
   cd newslaunch
   ```

2. Create a new virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install development and test dependencies:

   ```bash
   pip install -e '.[test]'
   ```

4. Use the Makefile to run the linter and tests:

   ```bash
   make fmt
   make test
   ```

## Example Project: newspad

The `newspad` directory contains an example of how to use the newslaunch package along with Terraform and additional Python code for a producer and a consumer to interact with an AWS Kinesis stream.

### Setup Instructions

1. Navigate to the `newspad` directory:

   ```bash
   cd newspad
   ```

2. Follow the setup instructions provided in the newspad/README.md to deploy the infrastructure using Terraform and run the example producer and consumer.
