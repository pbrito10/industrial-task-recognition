FROM python:3.12.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libdbus-1-3 \
        libgl1 \
        libglib2.0-0 \
        libgtk-3-0 \
        libportaudio2 \
        libsm6 \
        libv4l-0 \
        libx11-6 \
        libxcb-cursor0 \
        libxcb-xinerama0 \
        libxcb1 \
        libxext6 \
        libxkbcommon-x11-0 \
        libxrender1 \
        v4l-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["python", "main.py"]
