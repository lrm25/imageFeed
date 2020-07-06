import scrapy

class SpacePornSpider(scrapy.Spider):

    name = "space-porn"

    def start_requests(self):
        urls = ["https://www.reddit.com/r/spaceporn"]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        print(response.css('a[data-click-id=body]').getall())