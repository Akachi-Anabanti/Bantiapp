#!/bin/bash
# Install poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies with poetry
poetry install

# Run migrations
poetry run flask db upgrade

# Start Gunicorn
poetry run gunicorn myblog:app