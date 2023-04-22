FROM python:3

VOLUME /image

RUN pip install scrapy
ADD imagefeed /imagefeed

WORKDIR /imagefeed/imagefeed
ENTRYPOINT ["/usr/local/bin/scrapy", "crawl", "space-porn", "-a", "imagepath=/image", "-a", "htmllocation=/image/image.html", "-a", "relativeimagepath=true"]
