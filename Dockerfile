FROM python:3.10.9-slim

ENV HOME=/home/srpantano

WORKDIR ${HOME}

RUN set -eux; \
    apt-get update; \
    apt-get install -y \
    build-essential \
    git 

RUN useradd -ms /bin/bash srpantano

COPY fundamentus.py ${HOME}
COPY StockValueScraper.py ${HOME}

RUN git clone https://github.com/srpantano/stocks.git

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python", "StockValueScraper.py", "--url https://www.fundamentus.com.br/resultado.php",  "-dt 2020-12-18" ]