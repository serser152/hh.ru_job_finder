#!/bin/sh
celery -A tasks worker --loglevel=INFO &
streamlit run main.py