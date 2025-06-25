# Setup Instructions

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sample-project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
```

## Running the Application

### Development Mode

```bash
python -m src.main --debug
```

### Production Mode

```bash
python -m src.main --config production.yaml
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_main.py
```

## Configuration

The application uses YAML configuration files. Key settings include:

- `app.name`: Application name
- `app.version`: Application version
- `app.debug`: Debug mode flag
- `database.host`: Database host
- `database.port`: Database port
- `api.host`: API server host
- `api.port`: API server port

## Environment Variables

The following environment variables can be used:

- `APP_DEBUG`: Enable debug mode
- `APP_DATABASE_URL`: Database connection URL
- `APP_API_KEY`: API authentication key

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed
2. **Config errors**: Check YAML syntax in config files
3. **Permission errors**: Ensure proper file permissions
