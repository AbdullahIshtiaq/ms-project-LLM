# Moon Project Django

A Django-based news analysis application that processes financial news articles, extracts stock mentions, and detects important events.

## Project Setup

This guide will walk you through setting up the project from scratch, including creating a virtual environment, installing dependencies, and running migrations.

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd moon-project-django
```

### 2. Set Up a Virtual Environment

#### Windows

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

#### macOS/Linux

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory by copying the example file:

```bash
cp .env.example .env
```

Then edit the `.env` file to set your environment variables:

```
DEBUG=True
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
MARKETSTACK_API_KEY=your_marketstack_api_key_here
```

Replace `your_secret_key_here` with a secure random string, `your_alpha_vantage_api_key_here` with your Alpha Vantage API key, and `your_marketstack_api_key_here` with your Marketstack API key.

### 5. Run Database Migrations

```bash
# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### 6. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

### 7. Run the Development Server

```bash
python manage.py runserver
```

The application should now be running at `http://127.0.0.1:8000/`.

## Project Structure

- `news_analyzer/`: Main application directory
  - `article_processor.py`: Handles article processing and event detection
  - `models.py`: Database models
  - `utils.py`: Utility functions
  - `views.py`: View functions
  - `urls.py`: URL routing
  - `fetch_lse_stocks.py`: Fetches stock information from Alpha Vantage API
  - `fetch_lse_stocks_marketstack.py`: Fetches stock information from Marketstack API

## Features

- News article processing and storage
- Stock mention extraction
- Event detection and categorization
- Sentiment analysis
- User notifications
- LSE stock information fetching from Alpha Vantage API
- LSE stock information fetching from Marketstack API

## Stock Data Management

The application provides two methods for fetching LSE stock information:

1. **Alpha Vantage API**:
   ```bash
   python manage.py update_lse_stocks
   ```

2. **Marketstack API** (recommended):
   ```bash
   python manage.py update_lse_stocks_marketstack
   ```

The Marketstack implementation is recommended as it provides more comprehensive data in a single request.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure your database server is running
   - Verify your database credentials in the `.env` file

2. **Migration Errors**
   - Try running `python manage.py migrate --fake-initial` if initial migrations fail

3. **Dependency Issues**
   - Make sure you're using the correct Python version
   - Try reinstalling dependencies with `pip install -r requirements.txt --force-reinstall`

4. **API Issues**
   - Verify your API keys are correctly set in the `.env` file
   - Check if you've exceeded the API rate limits
   - For Marketstack API issues, refer to their [documentation](https://marketstack.com/documentation_v2)

## License

[Specify your license here] 