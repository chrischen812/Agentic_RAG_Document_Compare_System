#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Download SpaCy English model
python -m spacy download en_core_web_sm