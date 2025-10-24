class TestAuthenticationMiddleware:
    """Test authentication middleware"""

    def test_auth_check__valid_token__passes_authentication(
        self, e2e_client, mock_auth_middleware
    ):
        """Test valid token authentication"""
        # Arrange
        headers = {'Authorization': 'Bearer test-token'}

        # Act
        response = e2e_client.get('/test-file-id', headers=headers)

        # Assert
        assert response.status_code != 401

    def test_auth_check__missing_token__return_401(self, e2e_client):
        """Test missing token authentication"""
        # Arrange
        # No headers

        # Act
        response = e2e_client.get('/test-file-id')

        # Assert
        assert response.status_code == 401

    def test_auth_check__valid_session_token__passes_authentication(
        self, e2e_client, mock_auth_middleware
    ):
        """Test valid session token authentication"""
        # Arrange
        cookies = {'token': 'valid-session-token'}

        # Act
        response = e2e_client.get('/test-file-id', cookies=cookies)

        # Assert
        assert response.status_code != 401

    def test_auth_check__invalid_session_token__return_401(self, e2e_client):
        """Test invalid session token authentication"""
        # Arrange
        cookies = {'token': 'invalid-session-token'}

        # Act
        response = e2e_client.get('/test-file-id', cookies=cookies)

        # Assert
        assert response.status_code == 401
