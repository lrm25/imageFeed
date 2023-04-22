import ctypes
from datetime import datetime
import json
import logging
import os
import pathlib
from pathlib import Path
import platform
import subprocess
import time
import urllib

import scrapy

class SpacePornSpider(scrapy.Spider):
    ''' Spider that pulls image from reddit's spaceporn website'''

    name = "space-porn"

    _reddit_main_page = "https://www.reddit.com"
    _space_porn_main_page = "https://www.reddit.com/r/spaceporn"
    _image_title = None
    _submitter = None
    _full_image_path = None
    _help_called = False

    def __init__(self, category='', **kwargs):
        super().__init__(**kwargs)

        if hasattr(self, 'help'):
            if self.help == 'true':
                self.usage()
                # more graceful than throwing CloseSpider
                self._help_called = True
                return
            if self.help != 'false':
                raise ValueError('Invalid help value: ' + self.help)

        self.relative_image_path = False
        if hasattr(self, 'relativeimagepath'):
            if self.relativeimagepath == 'true':
                self.relative_image_path = True
            elif self.relativeimagepath != 'false':
                raise ValueError("Invalid relativeimagepath value: " + self.relativeimagepath)

        self.set_background = False
        if hasattr(self, 'background'):
            if self.background == 'true':
                self.set_background = True
            elif self.background != 'false':
                raise ValueError("Invalid background value: " + self.background)

    def usage(self):
        ''' Print usage when user specifies 'help' flag '''

        print("relativeimagepath: use relative image path in HTML file " +
            "(\'true\' or \'false\', default \'false\')")
        print('htmllocation: HTML file location (default:  image.html in working directory)')
        print('imagepath: folder to place images in (default:  working directory)')
        print('background:  set computer background (\'true\' or \'false\', default: \'false\')')
        print('help: display this help (\'true\' or \'false\', default: \'false\')')

    def start_requests(self):
        ''' Scrapy calls this to begin pulling image '''
        # exit if we just called 'help'
        if self._help_called:
            return
        yield scrapy.Request(self._space_porn_main_page, callback=self.parse_main_page,
                             errback=self.parse_error, dont_filter=True)

    def parse_error(self, failure):
        ''' Scrapy error callback '''

        logging.error(f"Error retreiving URL {failure.request_url}: {failure.value}")
        # timeouts give no status code, make sure this isn't a timeout
        if failure.value.response is not None:
            logging.error(f"Status code {failure.value.response.status} returned")

    def parse_main_page(self, response):
        ''' Go to main reddit spaceporn page, get page for image '''

        image_page_link = response.xpath('//*[a[@href]/div/div/img]/a/@href').get()
        if image_page_link is None:
            logging.error("Link to first image page not found in HTML")
            return
        first_image_page_url = self._reddit_main_page + image_page_link
        yield scrapy.Request(first_image_page_url, callback=self.parse_image_page)

    def parse_image_page(self, response):
        ''' Get image URL '''

        print(response.xpath('//*[a[img]]').get())
        submitter_string = response.xpath('//*[a[contains(@href,"/user/")]]/a/@href').get()
        self._submitter = submitter_string.split('/user/')[1][:-1]
        print("Submitter: " + self._submitter)
        self._image_title = response.xpath('//h1/text()').get()
        image_marker = response.xpath('//*[a[img[contains(@alt,"spaceporn")]]]/a/@href').get()
        if image_marker is None:
            logging.error("Link to image URL not found in HTML")
            return
        yield scrapy.Request(image_marker, callback=self.save_and_set_image)

    def file_exists(self, image_name):
        ''' Mockable function to check if file exists, for testing '''
        return os.path.isfile(image_name)

    file_exists_func = file_exists

    def write_to_file(self, file_location, file_name, data_bytes):
        ''' Mockable function to write to file, for testing '''
        with open(os.path.join(file_location, file_name), 'wb') as file:
            file.write(data_bytes)

    write_to_file_func = write_to_file

    def save_image(self, path, response):
        ''' Save the image to disk, if it hasn't been downloaded yet '''

        image_name = response.url.split('/')[-1]
        if '?' in image_name:
            image_name = image_name.split('?')[0]
        if '%' in image_name:
            image_name = urllib.parse.unquote(image_name)

        data = {
            "title": self._image_title,
            "file": image_name,
            "submitter": self._submitter
        }

        image_list = []

        duplicate = False

        json_file = Path('images.json')
        json_file.touch(exist_ok=True)
        with open(json_file, "r+") as json_file:
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
            logging.error(f"Unable to retrieve image name from url {response.url}")
            return None
        if self.file_exists_func(os.path.join(path, image_name)):
            logging.info(f"File {image_name} already downloaded")
            return image_name
        else:
            try:
                print(image_name)
                self.write_to_file_func(path, image_name, response.body)
            except IOError as e:
                logging.error(f"Unable to write to {image_name}:  {str(e)}")
                return None
        return image_name

    def check_platform(self):
        ''' Make sure this is a platform where program has been written to set background '''

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

        logging.error(f"System not supported (System: {system})")
        return False, ''

    def execute_gsettings_cmd(self, command):
        ''' Run linux/gnome gsettings command '''

        result = subprocess.run(command, stdout=subprocess.PIPE, text=True)

        error = False
        if result.stdout not in ("", None):
            error = True
            logging.error(f"STDOUT:  {result.stdout}")
        if result.stderr not in ("", None):
            error = True
            logging.error(f"STDERR:  {result.stderr}")
        if error:
            return False
        return True

    def set_image(self, background_supported, platform_str, image_name):
        ''' Write static HTML file containing image, and optionally set background '''

        html_location = ''
        if not hasattr(self, 'htmllocation'):
            html_location = os.path.join(os.getcwd(), 'image.html')
        else:
            html_location = self.htmllocation

        image_path = ''
        if self.relative_image_path:
            print("Html location: " + html_location)
            print("Full image path: " + self._full_image_path)
            image_path = os.path.relpath(self._full_image_path,
                os.path.dirname(os.path.abspath(html_location)))
        else:
            image_path = pathlib.Path(self._full_image_path).as_uri()

        if platform_str == 'Windows':
            if self.set_background and background_supported:
                SPI_SETBACKGROUND = 20
                ctypes.windll.user32.SystemParametersInfoW(SPI_SETBACKGROUND, 0,
                    os.path.join(image_path, image_name), 0)
            # Edit for HTML file
            image_path = image_path.replace('\\', '/')
        elif platform_str == 'Linux':
            file_url = f"file:///{image_path}/{image_name}"

        # write static HTML page
        html_page_data = '''<!DOCTYPE html>
            <head>
                <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"/>
                <meta http-equiv="Pragma" content="no-cache"/>
                <meta http-equiv="Expires" content="0"/>
            <title>Spaceporn</title>
            <style>body{
                background-color: black;
                background-position: center top;
                background-repeat: no-repeat;
                background-size: auto 100vh;
            }</style>
            </head>
            <body>
            <p style=\"color:white\">''' + self._image_title + '''</p>
            <p style=\"color:white\">Submitter: ''' + self._submitter + '''</p>
            <p style=\"color:white\">Retrieved ''' + \
                datetime.now().strftime("%B %d, %Y %I:%M:%S %p ") + \
                time.tzname[time.localtime().tm_isdst] + '''</p>
            <p id="test"></p>
            <script>
            document.body.style.backgroundImage = "url(\'''' + image_path + '''\')"
            </script>
            </body>
            </html>'''

        self.write_to_file_func(os.path.dirname(html_location), os.path.basename(html_location),
            bytes(html_page_data, 'utf-8'))

        if self.set_background and background_supported:
            if platform_str == 'Linux':
                # reset parameters to avoid any weird issues i've seen
                if not self.execute_gsettings_cmd(['gsettings', 'reset',
                        'org.gnome.desktop.background', 'picture-uri']):
                    return False

                if not self.execute_gsettings_cmd(['gsettings', 'reset',
                        'org.gnome.desktop.background', 'picture-options']):
                    return False

                if not self.execute_gsettings_cmd(['gsettings', 'set',
                        'org.gnome.desktop.background', 'picture-uri', file_url]):
                    return False

                if not self.execute_gsettings_cmd(['gsettings', 'set',
                        'org.gnome.desktop.background', 'picture-options', 'spanned']):
                    return False

        return True

    def save_and_set_image(self, response):
        ''' Save image, and optionally set to computer background based on what user selects '''

        image_location = os.getcwd()
        if hasattr(self, 'imagepath'):
            image_location = os.path.join(image_location, self.imagepath)

        image_name = self.save_image(image_location, response)
        if image_name is None:
            logging.error("Error saving image, exiting ...")
            return

        self._full_image_path = os.path.join(image_location, image_name)

        supported, platform_str = self.check_platform()

        if self.set_image(supported, platform_str, self._full_image_path):
            logging.info("Background set successful")
