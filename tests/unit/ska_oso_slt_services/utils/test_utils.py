from unittest.mock import patch

from ska_oso_slt_services.common.file_upload import upload_image_to_folder


class media_content:
    filename = "test/image.png"

    def save(self, path):
        self.path = path


media = media_content()


class TestImageUploadDownload:
    @patch("ska_oso_slt_services.common.file_upload.Image.open")
    def test_upload_image_to_folder(self, mock_open):
        mock_image = mock_open.return_value
        mock_image.size = (800, 600)

        # Set up the mock to return the mock image object
        mock_open.return_value = mock_image

        upload_image_to_folder(file_id="test", media_content=media)
