import ctypes
import json
import logging
import os
import pathlib
import platform
import scrapy
import subprocess

class SpacePornSpider(scrapy.Spider):

    name = "space-porn"

    _reddit_main_page = "https://www.reddit.com"
    _space_porn_main_page = "https://www.reddit.com/r/spaceporn"
    _image_title = None
    _submitter = None

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
        print(response.xpath('//*[a[img]]').get())
        submitter_string = response.xpath('//*[a[contains(@href,"/user/")]]/a/@href').get()
        self._submitter = submitter_string.split('/user/')[1][:-1]
        print("Submitter: " + self._submitter)
        self._image_title = response.xpath('//h1/text()').get()
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

        data = {
            "title": self._image_title,
            "file": image_name,
            "submitter": self._submitter
        }

        image_list = []

        duplicate = False
        with open("images.json", "r+") as json_file:
            if 0 < os.path.getsize("images.json"):
                image_list = json.load(json_file)
                print(image_list)

            for element in image_list:
                if "file" in element and element["file"] == image_name:
                    duplicate = True
                    break
            if not duplicate:
                image_list.append(data)
            else:
                print("duplicate found")

        if not duplicate:
            with open("images.json", "w") as json_file:
                json_data = json.dumps(image_list)
                json_file.write(json_data)

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
        if (system == 'Linux') and ('Ubuntu' in version):
            result = subprocess.run(['gsettings'], stderr=subprocess.PIPE)
            if 'Usage' not in str(result.stderr):
                logging.error("Ubuntu Linux, but system does not run gsettings")
                return False
            return True, 'Linux'

        # TODO specific versions
        if system == 'Windows':
            return True, 'Windows'
        
        logging.error("System and version not supported(System: {}, version: {})".
                      format(system, version))
        return False, ''

    def execute_gsettings_cmd(self, command):

        result = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True)

        error = False
        if result.stdout != "" and result.stdout != None:
            error = True
            logging.error("STDOUT:  {}".format(result.stdout))
        if result.stderr != "" and result.stderr != None:
            error = True
            logging.error("STDERR:  {}".format(result.stderr))
        if error:
            return False
        return True

    def set_image(self, platform, image_name):

        cwd = os.getcwd()
        print(os.listdir())
        if platform == 'Windows':
            SPI_SETBACKGROUND = 20
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETBACKGROUND, 0, os.path.join(cwd, image_name), 0)
        elif platform == 'Linux':
            file_url = "file:///{}/{}".format(cwd, image_name)

        html_page_data = "<html>\n \
            <head>Spaceporn</head>\n \
            <style>body{\n \
                background-image: url(\'" + pathlib.Path(os.path.join(cwd, image_name)).as_uri() + "\')\n \
            }</style>\n \
            </html>"
        print(html_page_data)

        self.write_to_file_func("test.html", bytes(html_page_data, 'utf-8'))
        
        if platform == 'Linux':
            # reset parameters to avoid any weird issues i've seen
            if not self.execute_gsettings_cmd(['gsettings', 'reset', 'org.gnome.desktop.background', 'picture-uri']):
                return False

            if not self.execute_gsettings_cmd(['gsettings', 'reset', 'org.gnome.desktop.background', 'picture-options']):
                return False

            if not self.execute_gsettings_cmd(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', file_url]):
                return False

            if not self.execute_gsettings_cmd(['gsettings', 'set', 'org.gnome.desktop.background', 'picture-options', 'spanned']):
                return False

        return True


    def save_and_set_image(self, response):

        image_name = self.save_image(response)
        if image_name == None:
            logging.error("Error saving image, exiting ...")
            return

        supported, platform = self.check_platform()
        if not supported:
            return

        if self.set_image(platform, image_name):
            logging.info("Background set successful")
