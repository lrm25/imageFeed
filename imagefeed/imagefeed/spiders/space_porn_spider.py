import os
import platform
import scrapy
import subprocess

class SpacePornSpider(scrapy.Spider):

    name = "space-porn"

    reddit_main_page = "https://www.reddit.com"
    space_porn_main_page = "https://www.reddit.com/r/spaceporn"

    def start_requests(self):
        urls = [self.space_porn_main_page]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        if response.url == self.space_porn_main_page:
            image_page_link = response.xpath('//*[a[@href]/div/div/img]/a/@href').get()
            first_image_page_url = self.reddit_main_page + image_page_link
            yield scrapy.Request(first_image_page_url, callback=self.parse_image_page)

    def parse_image_page(self, response):
        image_marker = response.xpath('//*[a[img[contains(@alt,"spaceporn")]]]/a/@href').get()
        yield scrapy.Request(image_marker, callback=self.save_and_set_image)

    def save_and_set_image(self, response):
        image_name = response.url.split('/')[-1]
        if os.path.isfile(image_name):
            print("File {} already downloaded".format(image_name))
            return

        with open(image_name, 'wb') as f:
            f.write(response.body)

        # make sure this is a ubuntu platform w/gsettings
        if (platform.system() != 'Linux') and ('Ubuntu' not in platform.version()):
            return
        
        result = subprocess.run(['gsettings'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if 'Usage' not in str(result.stderr):
            return

        result = subprocess.run(['pwd'], stdout=subprocess.PIPE, text=True)
        pwd = str(result.stdout).strip()
        file_url = "file:///{}/{}".format(pwd, image_name)
        result = subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', file_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        error = False
        if result.stdout != "":
            error = True
            print("STDOUT:  {}".format(result.stdout))
        if result.stderr != "":
            error = True
            print("STDERR:  {}".format(result.stderr))
        if not error:
            print("Background set successful")
                


