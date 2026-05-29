"""Tests for secure_filename function."""

from src.presentation.api.files import secure_filename


class TestSecureFilename:
    """Test secure_filename sanitization."""

    # --- Unicode preservation ---

    def test_secure__cyrillic__preserved(self):
        """Cyrillic characters are preserved."""
        # act & assert
        assert secure_filename('документ.pdf') == 'документ.pdf'

    def test_secure__chinese__preserved(self):
        """Chinese characters are preserved."""
        # act & assert
        assert secure_filename('报告.xlsx') == '报告.xlsx'

    def test_secure__mixed_unicode_ascii__preserved(self):
        """Mixed Unicode and ASCII preserved."""
        # act & assert
        result = secure_filename('отчёт_2024.pdf')
        assert result == 'отчёт_2024.pdf'

    def test_secure__korean__preserved(self):
        """Korean characters preserved."""
        # act & assert
        result = secure_filename('파일.txt')
        assert result == '파일.txt'

    # --- Safe ASCII ---

    def test_secure__simple_ascii__unchanged(self):
        """Simple ASCII filename unchanged."""
        # act & assert
        assert secure_filename('report.pdf') == 'report.pdf'

    def test_secure__dash_underscore__kept(self):
        """Dashes and underscores preserved."""
        # act & assert
        assert secure_filename('my-file_v2.txt') == 'my-file_v2.txt'

    # --- Dangerous characters replaced ---

    def test_secure__path_traversal__blocked(self):
        """Path traversal sequences blocked."""
        # act
        result = secure_filename('../../etc/passwd')

        # assert — slashes replaced, dots stripped
        assert '/' not in result
        assert '..' not in result

    def test_secure__backslash__replaced(self):
        """Backslashes replaced."""
        # act
        result = secure_filename('dir\\file.txt')

        # assert
        assert '\\' not in result

    def test_secure__shell_metachar__replaced(self):
        """Shell metacharacters replaced."""
        # act
        result = secure_filename('file;rm -rf.txt')

        # assert
        assert ';' not in result

    def test_secure__null_byte__replaced(self):
        """Null bytes replaced."""
        # act
        result = secure_filename('file\x00.txt')

        # assert
        assert '\x00' not in result

    # --- Edge cases ---

    def test_secure__empty__unnamed(self):
        """Empty string returns unnamed_file."""
        # act & assert
        assert secure_filename('') == 'unnamed_file'

    def test_secure__none__unnamed(self):
        """None returns unnamed_file."""
        # act & assert
        assert secure_filename(None) == 'unnamed_file'

    def test_secure__only_dots__unnamed(self):
        """Only dots returns unnamed_file."""
        # act & assert
        assert secure_filename('...') == 'unnamed_file'

    def test_secure__hidden_file__dot_stripped(self):
        """Leading dot stripped (no hidden files)."""
        # act
        result = secure_filename('.htaccess')

        # assert
        assert not result.startswith('.')

    def test_secure__spaces__collapsed(self):
        """Multiple spaces collapsed to underscore."""
        # act
        result = secure_filename('my   file.txt')

        # assert
        assert '   ' not in result
        assert '_' in result

    def test_secure__trailing_dots__stripped(self):
        """Trailing dots stripped (Windows FS)."""
        # act
        result = secure_filename('file...')

        # assert
        assert not result.endswith('.')

    def test_secure__multiple_underscores__collapsed(self):
        """Multiple underscores collapsed."""
        # act
        result = secure_filename('file___name.txt')

        # assert
        assert '___' not in result

    def test_secure__cyrillic_with_specials__preserved(self):
        """Cyrillic preserved but specials replaced."""
        # act
        result = secure_filename('файл<script>.pdf')

        # assert
        assert 'файл' in result
        assert '<' not in result
        assert '>' not in result
        assert result.endswith('.pdf')

    def test_secure__double_ext__preserved(self):
        """Double extension preserved."""
        # act & assert
        assert secure_filename('file.tar.gz') == 'file.tar.gz'

    def test_secure__very_long__handled(self):
        """Very long filename doesn't crash."""
        # arrange
        long_name = 'a' * 500 + '.txt'

        # act
        result = secure_filename(long_name)

        # assert — must return something valid, not crash
        assert isinstance(result, str)
        assert len(result) > 0
