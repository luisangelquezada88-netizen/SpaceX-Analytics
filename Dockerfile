FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ARG para dev local con notebooks: docker compose pasa EXTRAS=true.
# Render usa el valor por defecto (false) = solo dashboard mínimo, imagen ~60% más ligera.
ARG EXTRAS=false

# Reqs primero para aprovechar caché de capas
COPY requirements.dashboard.txt .
COPY requirements.txt .

# Producción: solo 6 paquetes (pandas, dash, plotly, folium...).
# Dev (EXTRAS=true): además full requirements + jupyterlab para el servicio notebooks.
RUN pip install --no-cache-dir -r requirements.dashboard.txt && \
    if [ "$EXTRAS" = "true" ]; then \
      pip install --no-cache-dir -r requirements.txt jupyterlab; \
    fi

# Solo lo que necesita el dashboard en Render. notebooks/ y tests/ se excluyen:
# van montados por volumen en compose dev y no se usan en prod.
COPY data/ data/
COPY app/ app/
COPY src/ src/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose dashboard port (Render inyecta $PORT, por defecto 8051)
EXPOSE 8051

# 1 worker + preload + threads: arranque frío más rápido y sin OOM en Free 512MB.
# 2 workers tardaba ~2x en despertar y Render ya sugiere WEB_CONCURRENCY=1.
# sh -c es necesario para expandir ${PORT}
CMD ["sh", "-c", "gunicorn app.spacex_dash_app:server --bind 0.0.0.0:${PORT:-8051} --workers 1 --threads 4 --preload --timeout 60"]
