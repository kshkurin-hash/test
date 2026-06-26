FROM python:3.12-slim

# Системные зависимости для X11 и SDL2
RUN apt-get update && apt-get install -y --no-install-recommends \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxrandr2 \
        libxi6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY logic.py gui.py ./

# Указываем SDL использовать X11 (не пытаться искать другие дисплейные бэкенды)
ENV SDL_VIDEODRIVER=x11
ENV PYTHONUNBUFFERED=1

CMD ["python", "gui.py"]
