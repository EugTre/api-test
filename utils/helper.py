import mimetypes
import requests
import allure


class Helper:
    """Class with helper functions"""

    @allure.step('Verification that given URI {uri} is an image')
    def is_image_url(self, uri):
        """Returns True if given URI is MIME type of image/...
        :param string uri: URI to test
        :return: boolean: True if URI is image/..., False otherwise
        """
        mime_type = mimetypes.guess_type(uri)[0]
        return mime_type[0:len('image')] == 'image'

    @allure.step('Get image by retrieved URL {url}')
    def allure_attach_image_by_url(self, url: str) -> None:
        """Downloads image from given URL and attaches to allure report

        Args:
          `url` (str) - URL to image."""
        response = requests.get(url, timeout=420)
        assert response.status_code == 200
        allure.attach(response.content, 'Acquired image', attachment_type=mimetypes.guess_type(url)[0])
