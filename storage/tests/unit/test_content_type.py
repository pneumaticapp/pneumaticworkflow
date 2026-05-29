"""Tests for Content-Type sanitization."""

from src.shared_kernel.security import sanitize_content_type


class TestSanitizeContentType:
    """Tests for sanitize_content_type function."""

    # --- Allowed types passthrough ---

    def test_sanitize__image_jpeg__passthrough(self):
        """Test image/jpeg passes through."""
        # arrange
        content_type = 'image/jpeg'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'image/jpeg'

    def test_sanitize__image_png__passthrough(self):
        """Test image/png passes through."""
        # arrange
        content_type = 'image/png'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'image/png'

    def test_sanitize__image_gif__passthrough(self):
        """Test image/gif passes through."""
        # arrange
        content_type = 'image/gif'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'image/gif'

    def test_sanitize__image_webp__passthrough(self):
        """Test image/webp passes through."""
        # arrange
        content_type = 'image/webp'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'image/webp'

    def test_sanitize__pdf__passthrough(self):
        """Test application/pdf passes through."""
        # arrange
        content_type = 'application/pdf'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/pdf'

    def test_sanitize__text_plain__passthrough(self):
        """Test text/plain passes through."""
        # arrange
        content_type = 'text/plain'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'text/plain'

    def test_sanitize__text_csv__passthrough(self):
        """Test text/csv passes through."""
        # arrange
        content_type = 'text/csv'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'text/csv'

    def test_sanitize__video_mp4__passthrough(self):
        """Test video/mp4 passes through."""
        # arrange
        content_type = 'video/mp4'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'video/mp4'

    def test_sanitize__json__passthrough(self):
        """Test application/json passes through."""
        # arrange
        content_type = 'application/json'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/json'

    def test_sanitize__octet_stream__passthrough(self):
        """Test application/octet-stream passes through."""
        # arrange
        content_type = 'application/octet-stream'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__zip__passthrough(self):
        """Test application/zip passes through."""
        # arrange
        content_type = 'application/zip'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/zip'

    def test_sanitize__audio_mpeg__passthrough(self):
        """Test audio/mpeg passes through."""
        # arrange
        content_type = 'audio/mpeg'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'audio/mpeg'

    # --- Blocked dangerous types ---

    def test_sanitize__text_html__blocked(self):
        """Test text/html is blocked (XSS vector)."""
        # arrange
        content_type = 'text/html'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__text_xml__blocked(self):
        """Test text/xml is blocked."""
        # arrange
        content_type = 'text/xml'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__xhtml__blocked(self):
        """Test application/xhtml+xml is blocked."""
        # arrange
        content_type = 'application/xhtml+xml'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__javascript__blocked(self):
        """Test application/javascript is blocked."""
        # arrange
        content_type = 'application/javascript'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__text_javascript__blocked(self):
        """Test text/javascript is blocked."""
        # arrange
        content_type = 'text/javascript'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__svg_xml__blocked(self):
        """Test image/svg+xml is blocked (XSS via SVG)."""
        # arrange
        content_type = 'image/svg+xml'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__ecmascript__blocked(self):
        """Test application/ecmascript is blocked."""
        # arrange
        content_type = 'application/ecmascript'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__x_javascript__blocked(self):
        """Test application/x-javascript is blocked."""
        # arrange
        content_type = 'application/x-javascript'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    # --- Edge cases ---

    def test_sanitize__none__octet_stream(self):
        """Test None input returns safe default."""
        # act
        result = sanitize_content_type(content_type=None)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__empty__octet_stream(self):
        """Test empty string returns safe default."""
        # act
        result = sanitize_content_type(content_type='')

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__unknown__octet_stream(self):
        """Test unknown MIME type returns safe default."""
        # arrange
        content_type = 'application/x-custom-dangerous'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__html_with_charset__blocked(self):
        """Test text/html with charset param is still blocked."""
        # arrange
        content_type = 'text/html; charset=utf-8'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__uppercase_html__blocked(self):
        """Test case-insensitive blocking."""
        # arrange
        content_type = 'TEXT/HTML'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__mixed_case_jpeg__passthrough(self):
        """Test case-insensitive matching for allowed types."""
        # arrange
        content_type = 'Image/JPEG'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'image/jpeg'

    def test_sanitize__jpeg_with_boundary__passthrough(self):
        """Test allowed type with extra params passes through."""
        # arrange
        content_type = 'image/jpeg; boundary=something'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'image/jpeg'

    def test_sanitize__whitespace_around__handled(self):
        """Test whitespace in content type is trimmed."""
        # arrange
        content_type = '  image/png  '

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'image/png'

    def test_sanitize__svg_mixed_case__blocked(self):
        """Test SVG blocking is case-insensitive."""
        # arrange
        content_type = 'Image/SVG+XML'

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == 'application/octet-stream'

    def test_sanitize__docx__passthrough(self):
        """Test Office docx passes through."""
        # arrange
        content_type = (
            'application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.document'
        )

        # act
        result = sanitize_content_type(content_type=content_type)

        # assert
        assert result == content_type
