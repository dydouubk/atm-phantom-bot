
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py contenu.json ./

RUN mkdir -p assets
COPY banner.png.png ./assets/banner.png

USER 10001

CMD ["python", "bot.py"]
