import pytest
from pneumatic_backend.services.markdown import MarkdownService


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('**Bold**', 'Bold'),
        ('*Italic*', '*Italic*'),
        ('***Bold Italic***', '*Bold Italic*'),
        ('Is ** *italic* inside bold**', 'Is  *italic* inside bold'),
        ('*Is **bold** inside italic*', '*Is bold inside italic*'),
        ('**Work\n in multiline**', 'Work\n in multiline'),
    ]
)
def test_clear_bold__ok(text, expected):

    # act
    result = MarkdownService._clear_bold(text)

    # assert
    assert result == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('**Bold**', '*Bold*'),
        ('*Italic*', 'Italic'),
        ('***Bold Italic***', '**Bold Italic**'),
        ('*Is **bold** inside italic*', 'Is bold inside italic'),
        ('*Work\n in multiline*', 'Work\n in multiline'),
    ]
)
def test_clear_italic__ok(text, expected):

    # act
    result = MarkdownService._clear_italic(text)

    # assert
    assert result == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        (
            '![[backend] Task, 🐛](https://g.com/07.png "attachment_id:2398")',
            '[backend] Task, 🐛'
        ),
        (
            'Embedded image:\n![image.jpg](https://storage.com/)',
            'Embedded image:\nimage.jpg'
        ),
        (
            'Embedded image:\n![some.jpg](https://storage.com/ "desc")',
            'Embedded image:\nsome.jpg',
        ),
        (
            '[name of link.webm](https://www.pneumatic.app/test.webm)',
            '[name of link.webm](https://www.pneumatic.app/test.webm)'
        )
    ]
)
def test_clear_images__ok(text, expected):

    # act
    result = MarkdownService._clear_images(text)

    # assert
    assert result == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        (
            '[some file.jpg](https://storage.googleapis.com/file.txt)',
            'some file.jpg',
        ),
        (
            '[some file.jpg](https://g.com/file.txt  "some description")',
            'some file.jpg',
        ),
        (
            'Hello, [file.jpg](https://g.com/file.txt  "desc") for you',
            'Hello, file.jpg for you',
        ),
        (
            'https://ama-assn.org/regeneron_photo.jpg',
            'https://ama-assn.org/regeneron_photo.jpg',
        ),
        (
            'Raw link https://ama-assn.org/regeneron_photo.jpg to file',
            'Raw link https://ama-assn.org/regeneron_photo.jpg to file',
        )
    ]
)
def test_clear_links__ok(text, expected):

    # act
    result = MarkdownService._clear_links(text)

    # assert
    assert result == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        (
            'This paragraph:\n\n2. One\n3. Two\n4. Three',
            'This paragraph:\n\nOne, Two, Three'
        ),
        (
            'This paragraph won\'t be converted '
            'because starting number is not 1. or -:\n\n'
            '* One\n'
            '* Two\n'
            '* Three',
            'This paragraph won\'t be converted '
            'because starting number is not 1. or -:\n\n'
            '* One\n'
            '* Two\n'
            '* Three'
        ),
        (
            'This paragraph will be converted:\n'
            '1. One\n'
            '2. Two\n'
            '  - Two.one\n'
            '  - Two.two\n'
            '    1. Two.two.one\n'
            '    1. Two.two.two\n'
            '3. Three',
            'This paragraph will be converted:\n'
            'One, Two, Two.one, Two.two, Two.two.one, Two.two.two, Three'
        ),
        (
            'First list:\n'
            '1. One\n'
            '2. Two\n'
            'Second list:\n'
            '1. Two.one\n'
            '    - Two.two\n',
            'First list:\n'
            'One, Two\n'
            'Second list:\n'
            'Two.one, Two.two'
        )
    ]
)
def test_clear_list__ok(text, expected):

    # act
    result = MarkdownService._clear_list(text)

    # assert
    assert result == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        ('[Nayantara Pat|6099] please', 'Nayantara Pat please'),
        ('**[12N@yantara-Pat|1]** please', '**12N@yantara-Pat** please'),
        (
            '[Man|9] please read [file.jpg](https://g.com/file.txt)',
            'Man please read [file.jpg](https://g.com/file.txt)'
        )
    ]
)
def test_clear_mentions__ok(text, expected):

    # act
    result = MarkdownService._clear_mentions(text)

    # assert
    assert result == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        (
            '| Heading 1 | Heading 2 |\n'
            '|---|---|\n'
            '| Line 1, cell 1 | Line 1, cell 2 |\n'
            '| Line 2, cell 1 | Line 2, cell 2 |\n\n',
            'Таблица\n'
        ),
        (
            '| Heading 1 |\n'
            '|---|\n'
            '| Line 1, cell 1 |\n'
            '| Line 2, cell 1 |\n\n',
            'Таблица\n'
        ),
        (
            '| Heading 1 | Heading 2 |\n'
            '|---|---|\n'
            '| Line 1, cell 1 | Line 1, cell 2 |\n'
            '| Line 2, cell 1 | Line 2, cell 2 |\n\n'
            '| Heading 1 | Heading 2 |\n'
            '|---|---|\n'
            '| Line 1, cell 1 | Line 1, cell 2 |\n'
            '| Line 2, cell 1 | Line 2, cell 2 |\n\n',
            'Таблица\n'
            'Таблица\n'
        ),
        # (
        #     '[Man|9] please read [file.jpg](https://g.com/file.txt)',
        #     'Man please read [file.jpg](https://g.com/file.txt)'
        # )
    ]
)
def test_clear_table__ok(text, expected):

    # act
    result = MarkdownService._clear_table(text)

    # assert
    assert result == expected


@pytest.mark.parametrize(
    ('text', 'expected'),
    [
        (
            '***[Mary@1 A-n|987] This paragraph*** will **bol\n'
            'd**:\n'
            '1. One ![image](https://go.net/img.jpg)\n'
            '2. Two [some file.jpg](https://g.com/file.txt)\n'
            '  - Two.one\n'
            '  - Two.*tw\no*\n\n'
            '| Heading 1 | Heading 2 |\n'
            '|---|---|\n'
            '| Line 1, cell 1 | Line 1, cell 2 |\n'
            '| Line 2, cell 1 | Line 2, cell 2 |\n\n'
            'End text https://g.com/file2.txt with link',
            'Mary@1 A-n This paragraph will bol\n'
            'd:\n'
            'One image, Two some file.jpg, Two.one, Two.tw\n'
            'o\n\n'
            'Таблица\n'
            'End text https://g.com/file2.txt with link',
        ),
        (
            '***[Mary@1 A-n|987] This paragraph*** will **bol\n'
            'd**:\n'
            '1. One ![image](https://go.net/img.jpg)\n'
            '2. Two [some file.jpg](https://g.com/file.txt)\n'
            '  - Two.one\n'
            '  - Two.*tw\no*\n'
            'End text https://g.com/file2.txt with link',
            'Mary@1 A-n This paragraph will bol\n'
            'd:\n'
            'One image, Two some file.jpg, Two.one, Two.tw\n'
            'o\n'
            'End text https://g.com/file2.txt with link',
        )
    ]
)
def test_clear__mixed_styles__ok(text, expected):

    # act
    result = MarkdownService.clear(text)

    # assert
    assert result == expected
