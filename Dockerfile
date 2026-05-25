FROM python:3.11-slim

WORKDIR /app

# System deps for Qdrant binary download and health checks
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Qdrant server binary (same major line as qdrant-client in requirements.txt)
RUN wget -q https://github.com/qdrant/qdrant/releases/download/v1.9.2/qdrant-x86_64-unknown-linux-musl.tar.gz \
    && tar -xzf qdrant-x86_64-unknown-linux-musl.tar.gz \
    && mv qdrant /usr/local/bin/qdrant \
    && rm qdrant-x86_64-unknown-linux-musl.tar.gz

RUN mkdir -p /app/qdrant_storage /app/db /app/storage/uploaded_files /app/storage/faq_files

COPY requirements-hf.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN sed -i 's/\r$//' /app/start_hf.sh && chmod +x /app/start_hf.sh

# Hugging Face Docker Spaces listen on 7860
EXPOSE 7860

CMD ["bash", "/app/start_hf.sh"]
