# pylint: disable=line-too-long
import pytest
from pneumatic_backend.services.html_converter import (
    RichEditorChecklistToHTMLService,
    convert_text_to_html,
)


class TestRichEditorChecklistToHTMLService:

    def test__call__two_checklist_items__ok(self):

        # arrange
        text = (
            '[clist:cl-1|cli-1]First item[/clist]\n'
            '[clist:cl-1|cli-2]Second item[/clist]\n'
        )
        expected = (
            '<ol>'
            '<li>First item</li>'
            '<li>Second item</li>'
            '</ol>\n'
        )

        # act
        response = RichEditorChecklistToHTMLService(text)()

        # assert
        assert expected == response

    def test__call__two_checklists__ok(self):

        # arrange
        text = (
            'Text before.\n'
            '[clist:cl-1|cli-1]First item[/clist]\n'
            '[clist:cl-1|cli-2]Second item[/clist]\n'
            'Text middle.\n'
            'Some text.\n'
            '[clist:cl-2|cli-1]Third item[/clist]\n'
            '[clist:cl-2|cli-2]Fourth item[/clist]\n'
            'Text after.'
        )
        expected = (
            'Text before.\n'
            '<ol>'
            '<li>First item</li>'
            '<li>Second item</li>'
            '</ol>\n'
            'Text middle.\n'
            'Some text.\n'
            '<ol>'
            '<li>Third item</li>'
            '<li>Fourth item</li>'
            '</ol>\n'
            'Text after.'
        )

        # act
        response = RichEditorChecklistToHTMLService(text)()

        # assert
        assert expected == response

    def test__call__included_markup__ok(self):

        # arrange
        text = (
            '[clist:cl-1|cli-1]***First item***[/clist]\n'
            '[clist:cl-1|cli-2]**Second {{field-1}} item**[/clist]\n'
            '[clist:cl-1|cli-3][link](http://go.com) to site[/clist]\n'
        )
        expected = (
            '<ol>'
            '<li><strong><em>First item</em></strong></li>'
            '<li><strong>Second {{field-1}} item</strong></li>'
            '<li><a href="http://go.com">link</a> to site</li>'
            '</ol>\n'
        )

        # act
        response = RichEditorChecklistToHTMLService(text)()

        # assert
        assert expected == response


def test__call__one_table__ok():
    # arrange
    text = (
        '| Heading 1 | Heading 2 |\n'
        '|---|---|\n'
        '| Line 1, cell 1 | Line 1, cell 2 |\n'
        '| Line 2, cell 1 | Line 2, cell 2 |\n\n'
    )
    expected = (
        '<table>\n'
        '<thead>\n'
        '<tr>\n'
        '<th>Heading 1</th>\n'
        '<th>Heading 2</th>\n'
        '</tr>\n'
        '</thead>\n'
        '<tbody>\n'
        '<tr>\n'
        '<td>Line 1, cell 1</td>\n'
        '<td>Line 1, cell 2</td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>Line 2, cell 1</td>\n'
        '<td>Line 2, cell 2</td>\n'
        '</tr>\n'
        '</tbody>\n'
        '</table>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert expected == response


def test__call__two_tables__ok():
    # arrange
    text = (
        '| Heading 1 | Heading 2 |\n'
        '|---|---|\n'
        '| Line 1, cell 1 | Line 1, cell 2 |\n'
        '| Line 2, cell 1 | Line 2, cell 2 |\n\n'
        '| Heading 3 | Heading 4 |\n'
        '|---|---|\n'
        '| Italics | *Italics* |\n'
        '| Bold | **Bold** |\n'
        '| Bold italics | ***Bold italics*** |\n'
        '| link | [Attach PO](https://storage.com/...tline.pdf)|\n\n'
    )
    expected = (
        '<table>\n'
        '<thead>\n'
        '<tr>\n'
        '<th>Heading 1</th>\n'
        '<th>Heading 2</th>\n'
        '</tr>\n'
        '</thead>\n'
        '<tbody>\n'
        '<tr>\n'
        '<td>Line 1, cell 1</td>\n'
        '<td>Line 1, cell 2</td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>Line 2, cell 1</td>\n'
        '<td>Line 2, cell 2</td>\n'
        '</tr>\n'
        '</tbody>\n'
        '</table>\n'
        '<table>\n'
        '<thead>\n'
        '<tr>\n'
        '<th>Heading 3</th>\n'
        '<th>Heading 4</th>\n'
        '</tr>\n'
        '</thead>\n'
        '<tbody>\n'
        '<tr>\n'
        '<td>Italics</td>\n'
        '<td><em>Italics</em></td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>Bold</td>\n'
        '<td><strong>Bold</strong></td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>Bold italics</td>\n'
        '<td><strong><em>Bold italics</em></strong></td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>link</td>\n'
        '<td><a href="https://storage.com/...tline.pdf">Attach PO</a></td>\n'
        '</tr>\n'
        '</tbody>\n'
        '</table>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert expected == response


def test__call__table_in_text__ok():
    # arrange
    text = (
        'Text before\n\n'
        '| Heading 1 | Heading 2 |\n'
        '|---|---|\n'
        '| Line 1, cell 1 | Line 1, cell 2 |\n'
        '| Line 2, cell 1 | Line 2, cell 2 |\n\n'
        'Text after\n'
    )
    expected = (
        '<p>Text before</p>\n'
        '<table>\n'
        '<thead>\n'
        '<tr>\n'
        '<th>Heading 1</th>\n'
        '<th>Heading 2</th>\n'
        '</tr>\n'
        '</thead>\n'
        '<tbody>\n'
        '<tr>\n'
        '<td>Line 1, cell 1</td>\n'
        '<td>Line 1, cell 2</td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>Line 2, cell 1</td>\n'
        '<td>Line 2, cell 2</td>\n'
        '</tr>\n'
        '</tbody>\n'
        '</table>\n'
        '<p>Text after</p>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test_convert_text_to_html__mixed_markup__ok():

    # arrange
    text = (
        'This paragraph will be converted to bullets list:\n\n'
        '- One\n'
        '2. Two\n'
        '- Three\n'
        '    - Three.one\n'
        '    - Three.two\n'
        '        - Three.two.one\n'
        '        - Three.two.two\n'
        '    - Three.three\n\n'
        '![image](https://go.net/img.jpg)'
    )
    expected = (
        '<p>This paragraph will be converted to bullets list:</p>\n'
        '<ul>\n'
        '<li>One</li>\n'
        '<li>Two</li>\n'
        '<li>Three<ul>\n'
        '<li>Three.one</li>\n'
        '<li>Three.two<ul>\n'
        '<li>Three.two.one</li>\n'
        '<li>Three.two.two</li>\n'
        '</ul>\n'
        '</li>\n'
        '<li>Three.three</li>\n'
        '</ul>\n'
        '</li>\n'
        '</ul>\n'
        '<p><img alt="image" src="https://go.net/img.jpg" /></p>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert expected == response


def test_convert_text_to_html__checklist__ok():

    # arrange
    text = (
        'Text before.\n\n'
        '- One\n'
        '2. Two\n'
        '- Three\n'
        '    - Three.one\n'
        '    - Three.two\n'
        '        - Three.two.one\n'
        '        - Three.two.two\n'
        '    1. Three.three\n\n'
        'Checklist title:\n'
        '[clist:cl-1|cli-1]***First item***[/clist]\n'
        '[clist:cl-1|cli-2]**Second {{field-1}} item**[/clist]\n'
        '[clist:cl-1|cli-3][link](http://go.com) to site[/clist]\n'
        '![image](https://go.net/img.jpg)\n'
        '[clist:cl-2|cli-5]![image](http://go.com/img.jpg)[/clist]\n'
        'Text after.\n'
    )
    expected = (
        '<p>Text before.</p>\n'
        '<ul>\n'
        '<li>One</li>\n'
        '<li>Two</li>\n'
        '<li>Three<ul>\n'
        '<li>Three.one</li>\n'
        '<li>Three.two<ul>\n'
        '<li>Three.two.one</li>\n'
        '<li>Three.two.two</li>\n'
        '</ul>\n'
        '</li>\n'
        '<li>Three.three</li>\n'
        '</ul>\n'
        '</li>\n'
        '</ul>\n'
        '<p>Checklist title:</p>\n'
        '<ol><li><strong><em>First item</em></strong></li>'
        '<li><strong>Second {{field-1}} item</strong></li>'
        '<li><a href="http://go.com">link</a> to site</li>'
        '</ol>\n'
        '<p><img alt="image" src="https://go.net/img.jpg" /></p>\n'
        '<ol>'
        '<li><img alt="image" src="http://go.com/img.jpg" /></li>'
        '</ol>\n'
        '<p>Text after.</p>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test_convert_text_to_html__mixed_items__ok():

    # arrange
    text = (
        'Checklist title:\n'
        '[clist:cl-1|cli-1]The list, item 1[/clist]\n'
        '[clist:cl-1|cli-2]The list, item 2[/clist]\n'
        '*Italics*\n\n'
        '**Bold**\n\n'
        '***Bold italics***\n\n'
        '[Attach PO](https://storage.com/...tline.pdf)\n\n'
        '| Heading 1 | Heading 2 |\n'
        '|---|---|\n'
        '| Line 1, cell 1 | Line 1, cell 2 |\n'
        '| Line 2, cell 1 | Line 2, cell 2 |\n\n'
        'The text after the table.\n\n'
        '| Heading 3 | Heading 4 |\n'
        '|---|---|\n'
        '| Italics | *Italics* |\n'
        '| Bold | **Bold** |\n'
        '| Bold italics | ***Bold italics*** |\n'
        '| link | [Attach PO](https://storage.com/...tline.pdf)|\n\n'
        'The text after the table.\n'
    )
    expected = (
        '<p>Checklist title:</p>\n'
        '<ol><li>The list, item 1</li><li>The list, item 2</li></ol>\n'
        '<p><em>Italics</em></p>\n'
        '<p><strong>Bold</strong></p>\n'
        '<p><strong><em>Bold italics</em></strong></p>\n'
        '<p><a href="https://storage.com/...tline.pdf">Attach PO</a></p>\n'
        '<table>\n'
        '<thead>\n'
        '<tr>\n'
        '<th>Heading 1</th>\n'
        '<th>Heading 2</th>\n'
        '</tr>\n'
        '</thead>\n'
        '<tbody>\n'
        '<tr>\n'
        '<td>Line 1, cell 1</td>\n'
        '<td>Line 1, cell 2</td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>Line 2, cell 1</td>\n'
        '<td>Line 2, cell 2</td>\n'
        '</tr>\n'
        '</tbody>\n'
        '</table>\n'
        '<p>The text after the table.</p>\n'
        '<table>\n'
        '<thead>\n'
        '<tr>\n'
        '<th>Heading 3</th>\n'
        '<th>Heading 4</th>\n'
        '</tr>\n'
        '</thead>\n'
        '<tbody>\n'
        '<tr>\n'
        '<td>Italics</td>\n'
        '<td><em>Italics</em></td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>Bold</td>\n'
        '<td><strong>Bold</strong></td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>Bold italics</td>\n'
        '<td><strong><em>Bold italics</em></strong></td>\n'
        '</tr>\n'
        '<tr>\n'
        '<td>link</td>\n'
        '<td><a href="https://storage.com/...tline.pdf">Attach PO</a></td>\n'
        '</tr>\n'
        '</tbody>\n'
        '</table>\n'
        '<p>The text after the table.</p>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert expected == response


def test__call__skip_first_number__ok():

    # arrange
    text = (
        'This paragraph:\n\n'
        '2. One\n'
        '3. Two\n'
        '4. Three'
    )
    expected = (
        '<p>This paragraph:</p>\n'
        '<ol>\n'
        '<li>One</li>\n'
        '<li>Two</li>\n'
        '<li>Three</li>\n'
        '</ol>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert expected == response


@pytest.mark.parametrize('symbol', ['*', '-', '+'])
def test__call__symbol_list__ok(symbol):

    # arrange
    text = (
        'This paragraph will be converted: \n\n'
        f'{symbol} One\n'
        f'{symbol} Two\n'
        f'{symbol} Three'
    )
    expected = (
        '<p>This paragraph will be converted: </p>\n'
        '<ul>\n'
        '<li>One</li>\n'
        '<li>Two</li>\n'
        '<li>Three</li>\n'
        '</ul>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test__call__list_in_text__ok():

    # arrange
    text = (
        'Text before\n\n'
        '* One\n'
        '* Two\n\n'
        'Text after\n'
    )
    expected = (
        '<p>Text before</p>\n'
        '<ul>\n'
        '<li>One</li>\n'
        '<li>Two</li>\n'
        '</ul>\n'
        '<p>Text after</p>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test__call__not_solidus_list__ignore():

    # arrange
    text = (
        'This paragraph won\'t be converted '
        'because starting number is not 1. or -:\n\n'
        '/ One\n'
        '/ Two\n'
        '/ Three'
    )
    expected = (
        '<p>This paragraph won\'t be converted '
        'because starting number is not 1. or -:</p>\n'
        '<p>/ One\n'
        '/ Two\n'
        '/ Three</p>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test__call__same_number__ok():

    # arrange
    text = (
        'This paragraph will be converted:\n\n'
        '1. One\n'
        '2. Two\n'
        '  - Two.one\n'
        '  - Two.two\n'
        '    1. Two.two.one\n'
        '    1. Two.two.two\n'
        '3. Three'
    )
    expected = (
        '<p>This paragraph will be converted:</p>\n'
        '<ol>\n'
        '<li>One</li>\n'
        '<li>Two</li>\n'
        '<li>Two.one</li>\n'
        '<li>Two.two<ol>\n'
        '<li>Two.two.one</li>\n'
        '<li>Two.two.two</li>\n'
        '</ol>\n'
        '</li>\n'
        '<li>Three</li>\n'
        '</ol>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test__call__broken__first_indent__skip():

    # arrange
    text = (
        'This paragraph will be converted to bullet list '
        'started from One:\n\n'
        ' - One\n'
        '2. Two\n'
        '- Three\n'
    )
    expected = (
        '<p>This paragraph will be converted to bullet list '
        'started from One:</p>\n'
        '<ul>\n'
        '<li>One</li>\n'
        '<li>Two</li>\n'
        '<li>Three</li>\n'
        '</ul>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test__multiline_text__ok():

    # arrange
    text = (
        '**Row one**\n'
        'Row two.\n\n'
        '1 Row three.'
    )
    expected = (
        '<p><strong>Row one</strong></p>\n'
        '<p>Row two.</p>\n'
        '<p>1 Row three.</p>'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


class TestFixConverterToHTMLService:
    def test__call__list_in_text__ok(self):
        # arrange
        text = (
            'Text before\n'
            '- One\n'
            '- Two\n\n'
            'Text after\n'
        )
        expected = (
            '<p>Text before</p>\n'
            '<ul>\n'
            '<li>One</li>\n'
            '<li>Two</li>\n'
            '</ul>\n'
            '<p>Text after</p>'
        )

        # act
        response = convert_text_to_html(text)

        # assert
        assert response == expected

    def test__call__two_tables_in_text__ok(self):
        # arrange
        text = (
            'One:\n'
            '| Heading 1 | Heading 2 |\n'
            '|---|---|\n'
            '| Line 1, cell 1 | Line 1, cell 2 |\n'
            '| Line 2, cell 1 | Line 2, cell 2 |\n'
            'Two:\n'
            '| Heading 3 | Heading 4 |\n'
            '|---|---|\n'
            '| Italics | *Italics* |\n'
            '| Bold | **Bold** |\n'
            'End\n'
        )
        expected = (
            '<p>One:</p>\n'
            '<table>\n'
            '<thead>\n'
            '<tr>\n'
            '<th>Heading 1</th>\n'
            '<th>Heading 2</th>\n'
            '</tr>\n'
            '</thead>\n'
            '<tbody>\n'
            '<tr>\n'
            '<td>Line 1, cell 1</td>\n'
            '<td>Line 1, cell 2</td>\n'
            '</tr>\n'
            '<tr>\n'
            '<td>Line 2, cell 1</td>\n'
            '<td>Line 2, cell 2</td>\n'
            '</tr>\n'
            '</tbody>\n'
            '</table>\n'
            '<p>Two:</p>\n'
            '<table>\n'
            '<thead>\n'
            '<tr>\n'
            '<th>Heading 3</th>\n'
            '<th>Heading 4</th>\n'
            '</tr>\n'
            '</thead>\n'
            '<tbody>\n'
            '<tr>\n'
            '<td>Italics</td>\n'
            '<td><em>Italics</em></td>\n'
            '</tr>\n'
            '<tr>\n'
            '<td>Bold</td>\n'
            '<td><strong>Bold</strong></td>\n'
            '</tr>\n'
            '</tbody>\n'
            '</table>\n'
            '<p>End</p>'
        )

        # act
        response = convert_text_to_html(text)

        # assert
        assert response == expected
