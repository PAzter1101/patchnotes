FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/generator \
    CONFIG_PATH=/data/config.yml \
    OUTPUT_DIR=/data/output \
    PROMPTS_DIR=/data/prompts

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home patchnotes

WORKDIR /app

COPY admin/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/generator/
COPY prompts/ /app/prompts/
COPY admin/ /app/admin/
COPY mkdocs/mkdocs.yml /app/mkdocs-default.yml

RUN chown -R patchnotes:patchnotes /app

USER patchnotes

EXPOSE 8501

CMD ["streamlit", "run", "admin/admin_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--client.toolbarMode=minimal"]
