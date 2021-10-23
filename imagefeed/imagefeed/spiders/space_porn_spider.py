import ctypes
from datetime import datetime
import json
import logging
import os
import pathlib
import platform
import scrapy
import subprocess
import sys

from scrapy.exceptions import CloseSpider

class SpacePornSpider(scrapy.Spider):

    name = "space-porn"

    _reddit_main_page = "https://www.reddit.com"
    _space_porn_main_page = "https://www.reddit.com/r/spaceporn"
    _image_title = None
    _submitter = None
    _full_image_path = None

    def __init__(self, category='', **kwargs):
        super().__init__(**kwargs)

        if hasattr(self, 'help'):
            if self.help == 'true':
                self.usage()
                raise CloseSpider('Help specified')
            elif self.help != 'false':
                raise Exception('Invalid help value: ' + self.help)

        self.relative_image_path = False
        if hasattr(self, 'relativeimagepath'): 
            if self.relativeimagepath == 'true':
                self.relative_image_path = True
            elif self.relativeimagepath != 'false':
                raise Exception("Invalid relativeimagepath value: " + self.relativeimagepath)

        self.set_background = False
        if hasattr(self, 'background'):
            if self.background == 'true':
                self.set_background = True
            elif self.background != 'false':
                raise Exception("Invalid background value: " + self.background)

    def usage(self):
        print("relativeimagepath: use relative image path in HTML file (\'true\' or \'false\', default \'false\)")
        print('htmllocation: HTML file location (default:  image.html in working directory)')
        print('imagepath: folder to place images in (default:  workinig directory)')
        print('background:  set computer background (\'true\' or \'false\', default: \'false\'')
        print("help: display this help (\'true\' or \'false\', default: \'false\'")

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
    def write_to_file(self, file_location, file_name, data_bytes):
        with open(os.path.join(file_location, file_name), 'wb') as file:
            file.write(data_bytes)

    write_to_file_func = write_to_file

    # save the image to disk, or skip if the newest image has already been downloaded
    def save_image(self, path, response):

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
        if self.file_exists_func(os.path.join(path, image_name)):
            logging.info("File {} already downloaded".format(image_name))
            return image_name
        else:
            try:
                self.write_to_file_func(path, image_name, response.body)
            except IOError as e:
                logging.error("Unable to write to {}:  {}". format(image_name, str(e)))
                return None
        return image_name 

    # make sure this is a ubuntu platform w/gsettings, or windows
    def check_platform(self):

        system = platform.system()
        # version = platform.version()
        if system == 'Linux':
            result = subprocess.run(['gsettings'], stderr=subprocess.PIPE)
            if 'Usage' not in str(result.stderr):
                logging.error("Linux, but system does not run gsettings")
                return False
            return True, 'Linux'

        # TODO specific versions
        if system == 'Windows':
            return True, 'Windows'
        
        logging.error("System not supported (System: {})".format(system))
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

    def set_image(self, background_supported, platform, image_name):

        html_location = ''
        if not hasattr(self, 'htmllocation'):
            html_location = os.path.join(os.getcwd(), 'image.html')
        else:
            html_location = self.htmllocation


        image_path = ''
        if self.relative_image_path: 
            print("Html location: " + html_location)
            print("Full image path: " + self._full_image_path)
            image_path = os.path.relpath(self._full_image_path, os.path.dirname(os.path.abspath(html_location)))
        else:
            image_path = pathlib.Path(self._full_image_path).as_uri()
        

        if platform == 'Windows':
            if self.set_background and background_supported:
                SPI_SETBACKGROUND = 20
                ctypes.windll.user32.SystemParametersInfoW(SPI_SETBACKGROUND, 0, os.path.join(image_path, image_name), 0)
            # Edit for HTML file
            image_path = image_path.replace('\\', '/')
        elif platform == 'Linux':
            file_url = "file:///{}/{}".format(image_path, image_name)

        html_page_data = "<html>\n \
            <head><title>Spaceporn</title>\n \
            <style>body{\n \
                background-color: black;\n \
                background-image: url(\'" + image_path + "\');\n \
                background-position: center top;\n \
                background-repeat: no-repeat;\n \
                background-size: auto 100vh;\n \
            }</style>\n \
            </head>\n \
            <body>\n \
            <p style=\"color:white\">" + self._image_title + "</p>\n \
            <p style=\"color:white\">Submitter: " + self._submitter + "</p>\n \
            <p style=\"color:white\">Retrieved " + datetime.now().strftime("%B %m, %Y %I:%M:%S %p") + "</p>\n \
            </body> \n \
            </html>"
        print(html_page_data)
        print("HTML location: " + html_location)

        self.write_to_file_func(os.path.dirname(html_location), os.path.basename(html_location), bytes(html_page_data, 'utf-8'))
        
        if self.set_background and background_supported:
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
        
        image_location = os.getcwd()
        if hasattr(self, 'imagepath'):
            image_location = os.path.join(image_location, self.imagepath)

        image_name = self.save_image(image_location, response)
        if image_name == None:
            logging.error("Error saving image, exiting ...")
            return
        
        self._full_image_path = os.path.join(image_location, image_name)

        supported, platform = self.check_platform()

        if self.set_image(supported, platform, self._full_image_path):
            logging.info("Background set successful")
