FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --create-home appuser && mkdir /app/data && chown appuser:appuser /app/data
ENV DATABASE_URL=sqlite:////app/data/restaurant.db APP_ENV=production LOG_LEVEL=INFO
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "restaurant_orders.api:app", "--host", "0.0.0.0", "--port", "8000"]
