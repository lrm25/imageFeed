import twisted
import unittest
import urllib

from mock import patch
from imagefeed.spiders.space_porn_spider import SpacePornSpider
    
class Response:
    status = 230

class Value:
    response = Response()

class Request:
    url = "value"

class Failure:
    request = Request()
    value = Value()

class TestSpacePorn(unittest.TestCase):

    @patch('imagefeed.spiders.space_porn_spider.logging')
    def test_parse_error(self, mock_logging):
        failure = Failure()
        sps = SpacePornSpider()
        sps.parse_error(failure)
        assert(mock_logging.error.called)

if __name__ == '__main__':
    unittest.main()
