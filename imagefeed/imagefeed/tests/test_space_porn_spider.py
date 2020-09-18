import scrapy
import twisted
import unittest
import urllib

from mock import Mock, patch
from imagefeed.spiders.space_porn_spider import SpacePornSpider
    
class Response:
    def __init__(self, status):
        self.status = status

class Value:
    def __init__(self, response):
        self.response = response

class Request:
    def __init__(self, url):
        self.url = url

class Failure:
    def __init__(self, request, value):
        self.request = request
        self.value = value

# TODO: may be able to combine these classes
# TODO: more info on patching
class SetupMockFileExists(object):
    
    def __init__(self, sps: SpacePornSpider, ret_val: bool):
        self.sps = sps
        self._orig_file_exists_func = sps.file_exists
        self.ret_val = ret_val

    def __enter__(self):
        self.sps.file_exists_func = self._test_file_exists_func

    def __exit__(self, type, value, traceback):
        self.sps.file_exists_func = self._orig_file_exists_func
    
    def _test_file_exists_func(self, image_name):
        return self.ret_val

class SetupMockWriteToFile(object):

    def __init__(self, sps: SpacePornSpider, dummy_error: str):
        self.sps = sps
        self._orig_func = sps.write_to_file
        self._dummy_error = dummy_error

    def __enter__(self):
        self.sps.write_to_file_func = self._test_write_to_file_func

    def __exit__(self, type, value, traceback):
        self.sps.write_to_file_func = self._orig_func
    
    def _test_write_to_file_func(self, image_name, data):
        if self._dummy_error:
            raise IOError(self._dummy_error)

class TestSpacePorn(unittest.TestCase):

    _main_page_data = '<div class="_3JgI-GOrkmyIeDeyzXdyUD _2CSlKHjH7lsjx0IpjORx14"><a href="/r/spaceporn/comments/iqrlsz/venusleft_titanmiddle_california_currentlyright/"><div class="_3Oa0THmZ3f5iZXAQ0hBJ0k " style="max-height:512px;margin:0 auto"><div><img alt="Post image" class="_2_tDEnGMLxpM6uOa2kaDB3 ImageBox-image media-element _1XWObl-3b9tPy64oaG6fax" src="https://preview.redd.it/i0t9cygn4jm51.jpg?width=640&amp;crop=smart&amp;auto=webp&amp;s=0517350ac5972b94d0e32ddf3b34a90093b7f523" style="max-height:512px"></div></div></a></div>'
    _image_page_data = '<div class="_3Oa0THmZ3f5iZXAQ0hBJ0k " style="margin:0 auto"><a href="https://i.redd.it/5urgv13z7tm51.jpg" target="_blank"><img alt="r/spaceporn - Last nights efforts. Taken with my phone." class="_2_tDEnGMLxpM6uOa2kaDB3 ImageBox-image media-element _1XWObl-3b9tPy64oaG6fax" src="https://preview.redd.it/5urgv13z7tm51.jpg?width=960&amp;crop=smart&amp;auto=webp&amp;s=70676554dd926d866d5f0d7d02e4ac05db24a41a" style="max-height:700px"></a></div>'

    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_parse_error_timeout(self, mock_logging):
        failure = Failure(Request("dontcare"), Value(None))
        sps = SpacePornSpider()
        sps.parse_error(failure)
        self.assertEqual(1, len(mock_logging.method_calls), "Only one error should be logged")
    
    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_parse_error_code(self, mock_logging):
        error_code = 500
        failure = Failure(Request("dontcare"), Value(Response(error_code)))
        sps = SpacePornSpider()
        sps.parse_error(failure)
        self.assertEqual(2, len(mock_logging.method_calls), "Two errors should be logged")
        self.assertIn(str(error_code), str(mock_logging.method_calls[1]))

    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_parse_main_page_xpath_not_found(self, mock_logging):
        response = scrapy.http.HtmlResponse(url="dontcare", body=str.encode("<body></body>",
            'UTF-8'))
        sps = SpacePornSpider()
        for response in sps.parse_main_page(response):
            continue
        self.assertEqual(1, len(mock_logging.method_calls), "One error should be logged")
    
    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_parse_main_page_xpath_found(self, mock_logging):
        response = scrapy.http.HtmlResponse(url="dontcare", body=str.encode(self._main_page_data,
            'UTF-8'))
        sps = SpacePornSpider()
        for response in sps.parse_main_page(response):
            continue
        self.assertEqual(0, len(mock_logging.method_calls), "No errors should be logged")

    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_parse_image_page_xpath_not_found(self, mock_logging):
        response = scrapy.http.HtmlResponse(url="dontcare", body=str.encode("<body></body>",
            'UTF-8'))
        sps = SpacePornSpider()
        for response in sps.parse_image_page(response):
            continue
        self.assertEqual(1, len(mock_logging.method_calls), "One error should be logged")
    
    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_parse_image_page_xpath_found(self, mock_logging):
        response = scrapy.http.HtmlResponse(url="dontcare", body=str.encode(self._image_page_data,
            'UTF-8'))
        sps = SpacePornSpider()
        for response in sps.parse_image_page(response):
            continue
        self.assertEqual(0, len(mock_logging.method_calls), "No errors should be logged")

    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_save_image_malformed_url(self, mock_logging):
        response = scrapy.http.HtmlResponse(url="/", body=None)
        sps = SpacePornSpider()
        test = sps.save_image(response)
        self.assertEqual(None, test, "save_image should return None")
        self.assertEqual(1, len(mock_logging.method_calls), "Should be one error")
        self.assertTrue("url" in str(mock_logging.method_calls[0]))

    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_save_image_already_exists(self, mock_logging):
        dummy_image_name = "a"
        response = scrapy.http.HtmlResponse(url=dummy_image_name, body=None)
        sps = SpacePornSpider()
        with SetupMockFileExists(sps, True):
            test = sps.save_image(response)
            self.assertEqual(dummy_image_name, test, "save_image should return {}".format(dummy_image_name))
            self.assertEqual(1, len(mock_logging.method_calls), "Should be one info statement")
            self.assertTrue("info" in str(mock_logging.method_calls[0]))
    
    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_save_image_write_error(self, mock_logging):
        dummy_image_name = "a"
        response = scrapy.http.HtmlResponse(url=dummy_image_name, body=None)
        sps = SpacePornSpider()
        with SetupMockFileExists(sps, False):
            dummy_error = "dummy error"
            with SetupMockWriteToFile(sps, dummy_error): 
                test = sps.save_image(response)
                self.assertEqual(None, test, "save_image should return {}".format(dummy_image_name))
                self.assertEqual(1, len(mock_logging.method_calls), "Should be one error statement")
                self.assertTrue(dummy_error in str(mock_logging.method_calls[0]))
    
    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_save_image_ok(self, mock_logging):
        dummy_image_name = "a"
        response = scrapy.http.HtmlResponse(url=dummy_image_name, body=None)
        sps = SpacePornSpider()
        with SetupMockFileExists(sps, False):
            with SetupMockWriteToFile(sps, None): 
                test = sps.save_image(response)
                self.assertEqual(dummy_image_name, test, "save_image should return {}".format(dummy_image_name))
                self.assertEqual(0, len(mock_logging.method_calls), "Should be no logger statements")

    _platform_system = "dontcare"
    def mock_platform_system(self):
        return self._platform_system
    
    _platform_version = "dontcare"
    def mock_platform_version(self):
        return self._platform_version

    @patch('imagefeed.spiders.space_porn_spider.platform')
    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_check_platform_invalid_system(self, mock_logging, mock_platform):
        mock_platform.system = self.mock_platform_system
        mock_platform.version = self.mock_platform_system
        sps = SpacePornSpider()
        test = sps.check_platform()
        self.assertFalse(test)
        self.assertTrue("dontcare" in str(mock_logging.method_calls[0]),
            "{} should be in {}".format("dontcare", str(mock_logging.method_calls[0])))

    _gsettings_error = "Usag"
    def mock_suprocess_call(self, command, stderr):
        mock_result = Mock()
        mock_result.stderr = self._gsettings_error
        return mock_result
    
    @patch('imagefeed.spiders.space_porn_spider.subprocess')
    @patch('imagefeed.spiders.space_porn_spider.platform')
    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_check_platform_no_gsettings(self, mock_logging, mock_platform, mock_subprocess):
        self._platform_system = "Linux"
        mock_platform.system = self.mock_platform_system
        self._platform_version = "Ubuntu"
        mock_platform.version = self.mock_platform_version
        mock_subprocess.run = self.mock_suprocess_call
        sps = SpacePornSpider()
        test = sps.check_platform()
        self.assertFalse(test)
        self.assertTrue("gsettings" in str(mock_logging.method_calls[0]),
                        "gsettings error should be returned")
    
    @patch('imagefeed.spiders.space_porn_spider.subprocess')
    @patch('imagefeed.spiders.space_porn_spider.platform')
    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_check_platform_ok(self, mock_logging, mock_platform, mock_subprocess):
        self._platform_system = "Linux"
        mock_platform.system = self.mock_platform_system
        self._platform_version = "Ubuntu"
        mock_platform.version = self.mock_platform_version
        self._gsettings_error = "Usage"
        mock_subprocess.run = self.mock_suprocess_call
        sps = SpacePornSpider()
        test = sps.check_platform()
        self.assertTrue(test)
        self.assertEqual(0, len(mock_logging.method_calls))

if __name__ == '__main__':
    unittest.main()
