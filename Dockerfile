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

# Expose dashboard port (Render inyecta $PORT, por defecto 8051)
EXPOSE 8051

# Producción con gunicorn: 2 workers es lo máximo seguro en plan Free 512MB
# sh -c es necesario para expandir ${PORT}
CMD ["sh", "-c", "gunicorn app.spacex_dash_app:server --bind 0.0.0.0:${PORT:-8051} --workers 2 --threads 2 --timeout 120"]
