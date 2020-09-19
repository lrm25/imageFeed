import logging
import os
import platform
import scrapy
import subprocess

class SpacePornSpider(scrapy.Spider):

    name = "space-porn"

    _reddit_main_page = "https://www.reddit.com"
    _space_porn_main_page = "https://www.reddit.com/r/spaceporn"

    # get r/spaceporn's main page
    def start_requests(self):
        yield scrapy.Request(self._space_porn_main_page, callback=self.parse_main_page, 
                             errback=self.parse_error, dont_filter=True)

    # deal with any URL request errors
    def parse_error(self, failure):
        logging.error("Error retreiving URL {}: {}".format(
            failure.request.url, failure.value))
        # timeouts give no status code, make sure this isn't a timeout
        if failure.value.response is not None:
            logging.error("Status code {} returned".format(failure.value.response.status))

    # get link to page for top image
    def parse_main_page(self, response):
        image_page_link = response.xpath('//*[a[@href]/div/div/img]/a/@href').get()
        if image_page_link == None:
            logging.error("Link to first image page not found in HTML")
            return
        first_image_page_url = self._reddit_main_page + image_page_link
        yield scrapy.Request(first_image_page_url, callback=self.parse_image_page)

    # get URL for image itself
    def parse_image_page(self, response):
        image_marker = response.xpath('//*[a[img[contains(@alt,"spaceporn")]]]/a/@href').get()
        if image_marker == None:
            logging.error("Link to image URL not found in HTML")
            return
        yield scrapy.Request(image_marker, callback=self.save_and_set_image)

    # mockable function to check if file exists
    def file_exists(self, image_name):    
        return os.path.isfile(image_name)
    
    file_exists_func = file_exists

    # mockable function to write to file
    def write_to_file(self, file_name, data_bytes):
        with open(file_name, 'wb') as file:
            file.write(data_bytes)

    write_to_file_func = write_to_file

    # save the image to disk, or skip if the newest image has already been downloaded
    def save_image(self, response):
        image_name = response.url.split('/')[-1]
        if image_name == "":
            logging.error("Unable to retrieve image name from url {}".format(response.url))
            return None
        if self.file_exists_func(image_name):
            logging.info("File {} already downloaded".format(image_name))
            return image_name
        else:
            try:
                self.write_to_file_func(image_name, response.body)
            except IOError as e:
                logging.error("Unable to write to {}:  {}". format(image_name, str(e)))
                return None
        return image_name 

    # make sure this is a ubuntu platform w/gsettings
    def check_platform(self):
        system = platform.system()
        version = platform.version()
        if (system != 'Linux') or ('Ubuntu' not in version):
            logging.error("System is not Ubuntu linux (System: {}, version: {})".
                          format(system, version))
            return False
        
        result = subprocess.run(['gsettings'], stderr=subprocess.PIPE)
        if 'Usage' not in str(result.stderr):
            logging.error("System does not run gsettings")
            return False
        return True

    def set_image(self, image_name):

        result = subprocess.run(['pwd'], stdout=subprocess.PIPE, text=True)
        pwd = str(result.stdout).strip()
        file_url = "file:///{}/{}".format(pwd, image_name)
        result = subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', file_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        error = False
        if result.stdout != "":
            error = True
            logging.error("STDOUT:  {}".format(result.stdout))
        if result.stderr != "":
            error = True
            logging.error("STDERR:  {}".format(result.stderr))
        if error:
            return False
        return True


    def save_and_set_image(self, response):

        image_name = self.save_image(response)
        if image_name == None:
            logging.error("Error saving image, exiting ...")
            return

        if not self.check_platform():
            return

        if self.set_image(image_name):
            logging.info("Background set successful")