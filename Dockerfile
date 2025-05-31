# ============================
# ✅ Dockerfile EchoInStone (RunPod Ready)
# ============================

FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

# Installer dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git curl build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copier le projet
WORKDIR /app
COPY . /app

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Définir la commande de démarrage
CMD ["python3", "serverless_main.py"]

