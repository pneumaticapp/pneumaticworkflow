"""Tests for secure_filename function."""

from src.presentation.api.files import secure_filename

# --- Unicode preservation ---


def test_secure_filename__cyrillic__preserved():

    # act
    result = secure_filename('документ.pdf')

    # assert
    assert result == 'документ.pdf'


def test_secure_filename__chinese__preserved():

    # act
    result = secure_filename('报告.xlsx')

    # assert
    assert result == '报告.xlsx'


def test_secure_filename__mixed_unicode_ascii__preserved():

    # act
    result = secure_filename('отчёт_2024.pdf')

    # assert
    assert result == 'отчёт_2024.pdf'


def test_secure_filename__korean__preserved():

    # act
    result = secure_filename('파일.txt')

    # assert
    assert result == '파일.txt'


# --- Safe ASCII ---


def test_secure_filename__simple_ascii__unchanged():

    # act
    result = secure_filename('report.pdf')

    # assert
    assert result == 'report.pdf'


def test_secure_filename__dash_underscore__kept():

    # act
    result = secure_filename('my-file_v2.txt')

    # assert
    assert result == 'my-file_v2.txt'


# --- Dangerous characters replaced ---


def test_secure_filename__path_traversal__blocked():

    # act
    result = secure_filename('../../etc/passwd')

    # assert
    assert '/' not in result
    assert '..' not in result


def test_secure_filename__backslash__replaced():

    # act
    result = secure_filename('dir\\file.txt')

    # assert
    assert '\\' not in result


def test_secure_filename__shell_metachar__replaced():

    # act
    result = secure_filename('file;rm -rf.txt')

    # assert
    assert ';' not in result


def test_secure_filename__null_byte__replaced():

    # act
    result = secure_filename('file\x00.txt')

    # assert
    assert '\x00' not in result


# --- Edge cases ---


def test_secure_filename__empty__unnamed():

    # act
    result = secure_filename('')

    # assert
    assert result == 'unnamed_file'


def test_secure_filename__none__unnamed():

    # act
    result = secure_filename(None)

    # assert
    assert result == 'unnamed_file'


def test_secure_filename__only_dots__unnamed():

    # act
    result = secure_filename('...')

    # assert
    assert result == 'unnamed_file'


def test_secure_filename__hidden_file__dot_stripped():

    # act
    result = secure_filename('.htaccess')

    # assert
    assert not result.startswith('.')


def test_secure_filename__spaces__collapsed():

    # act
    result = secure_filename('my   file.txt')

    # assert
    assert '   ' not in result
    assert '_' in result


def test_secure_filename__trailing_dots__stripped():

    # act
    result = secure_filename('file...')

    # assert
    assert not result.endswith('.')


def test_secure_filename__multiple_underscores__collapsed():

    # act
    result = secure_filename('file___name.txt')

    # assert
    assert '___' not in result


def test_secure_filename__cyrillic_with_specials__preserved():

    # act
    result = secure_filename('файл<script>.pdf')

    # assert
    assert 'файл' in result
    assert '<' not in result
    assert '>' not in result
    assert result.endswith('.pdf')


def test_secure_filename__double_ext__preserved():

    # act
    result = secure_filename('file.tar.gz')

    # assert
    assert result == 'file.tar.gz'


def test_secure_filename__very_long__handled():

    # arrange
    long_name = 'a' * 500 + '.txt'

    # act
    result = secure_filename(long_name)

    # assert
    assert isinstance(result, str)
    assert len(result) > 0
