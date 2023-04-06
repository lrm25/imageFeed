FROM python:3

VOLUME /image

RUN pip install scrapy
ADD imagefeed /imagefeed
