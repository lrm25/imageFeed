import twisted
import unittest
import urllib

from mock import patch
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

class TestSpacePorn(unittest.TestCase):

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

if __name__ == '__main__':
    unittest.main()
