FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY data/ data/
COPY notebooks/ notebooks/
COPY app/ app/
COPY src/ src/
COPY tests/ tests/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose dashboard port
EXPOSE 8051

# Default command to run the dashboard
CMD ["python", "app/spacex_dash_app.py"]
