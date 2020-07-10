import scrapy

class SpacePornSpider(scrapy.Spider):

    name = "space-porn"

    reddit_main_page = "https://www.reddit.com"
    space_porn_main_page = reddit_main_page + "/r/spaceporn"

    def start_requests(self):
        urls = [self.space_porn_main_page]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        if response.url == self.space_porn_main_page:
            yield scrapy.Request(self.reddit_main_page + response.css('a[data-click-id=body]::attr(href)').get(),
            callback=self.parse_image_page)

    def parse_image_page(self, response):
        print(response.text)

