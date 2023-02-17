FROM python:3.10.9-slim

#RUN useradd -ms /bin/bash srpantano

#ENV HOME=/home/srpantano

ENV HOME=/app

WORKDIR ${HOME}

RUN set -eux; \
    apt-get update; \
    apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --progress --verbose https://github.com/srpantano/stocks.git .

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "StockValueScraper.py", "--url https://www.fundamentus.com.br/resultado.php",  "-dt 2020-12-18" ]