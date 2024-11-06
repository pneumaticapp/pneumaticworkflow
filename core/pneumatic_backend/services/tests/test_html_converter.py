# pylint: disable=line-too-long
import pytest
from django.conf import settings

from pneumatic_backend.services.html_converter import (
    RichEditorLinkToHtmlService,
    RichEditorBoldToHTMLService,
    RichEditorItalicToHTMLService,
    RichEditorImageToHTMLService,
    RichEditorListToHTMLService,
    RichEditorChecklistToHTMLService,
    RichEditorTableToHtmlService,
    convert_text_to_html,
)


class TestRichEditorLinkToHTMLService:
    @pytest.mark.parametrize(
        ('link', 'expected'), [
            (
                (
                    f'[regeneron_photo.jpg]'
                    f'(https://storage.googleapis.com/'
                    f'{settings.GCLOUD_BUCKET_NAME}/)'
                ),
                (
                    f'<a href="https://storage.googleapis.com/'
                    f'{settings.GCLOUD_BUCKET_NAME}/">'
                    f'regeneron_photo.jpg</a>'
                )
            ),
            (
                (
                    f'[name of link.webm]'
                    f'(https://www.pneumatic.app/test.webm'
                    f'  "some description")'
                ),
                (
                    f'<a href="https://www.pneumatic.app/test.webm">'
                    f'name of link.webm</a>'
                )
            )
        ]
    )
    def test_urls(self, link, expected):
        text = (
            'Hello, it is me, you favorite president,'
            ' and I want to offer you REGENERON\n'
            f'{link}\n'
            'REGENERON is a new experimental drug, that will cure you of...'
        )
        text_result = (
            'Hello, it is me, you favorite president,'
            ' and I want to offer you REGENERON\n'
            f'{expected}\n'
            'REGENERON is a new experimental drug, that will cure you of...'
        )
        assert RichEditorLinkToHtmlService(text)() == text_result

    def test_urls_not_on_mask_provided(self):
        regeneron_photo = (
            'https://ama-assn.org/regeneron_photo.jpg'
        )
        regeneron_terms = (
            'https://ama-assn.org/regeneron_terms_of_use.pdf'
        )
        text = f'''
            Hello, it is me, you favorite president,
            and I want to offer you REGENERON
            {regeneron_photo}
            REGENERON is a new experimental drug, that will cure you of
            coronaviruis in a couple days, just like me!
            Call now, and get it with a -50% discount!
            {regeneron_terms}
        '''

        assert RichEditorLinkToHtmlService(text)() == text


class TestRichEditorBoldItalicHTMLService:
    @pytest.mark.parametrize(
        ('text', 'expected'),
        [
            ('**Bold**', '<b>Bold</b>'),
            ('*Italic*', '<em>Italic</em>'),
            ('***Bold Italic***', '<em><b>Bold Italic</b></em>'),
            (
                'There is ** *italic* inside bold**',
                'There is <b> <em>italic</em> inside bold</b>'
            ),
            (
                '*There is **bold** inside italic*',
                '<em>There is <b>bold</b> inside italic</em>',
            ),
            (
                """**Bold work
                in multiline**
                """,
                """<b>Bold work
                in multiline</b>
                """
            ),
            (
                """*Italic work
                in multiline*
                """,
                """<em>Italic work
                in multiline</em>
                """
            )
        ]
    )
    def test_bold_italic(self, text, expected):
        # act
        text = RichEditorBoldToHTMLService(text)()
        response = RichEditorItalicToHTMLService(text)()

        # assert
        assert response == expected


class TestRichEditorImageToHTMLService:

    def test_call__alt__with_brackets__ok(self, mocker):

        # arrange
        mocker.patch(
            'pneumatic_backend.services.html_converter.'
            'RichEditorImageToHTMLService.style',
            new=''
        )
        text = (
            '![[back] Dec3, 1-07pm — 🐛 — New Step 3 - Pneumatic.png]'
            '(https://storage.googleapis.com/07.png '
            '"attachment_id:2398")'
        )
        expected = (
            '<img alt="[back] Dec3, 1-07pm — 🐛 — New Step 3 - Pneumatic.png"'
            ' src="https://storage.googleapis.com/07.png"/>'
        )

        # act
        response = RichEditorImageToHTMLService(text)()

        # assert
        assert response == expected

    def test_call___ok(self, mocker):

        # arrange
        mocker.patch(
            'pneumatic_backend.services.html_converter.'
            'RichEditorImageToHTMLService.style',
            new=''
        )
        text = (
            'Embedded image:\n'
            '![EucmaqmWQAkI3hR.jpg](https://storage.com/)'
        )
        expected = (
            'Embedded image:\n'
            '<img alt="EucmaqmWQAkI3hR.jpg" src="https://storage.com/"/>'
        )

        # act
        response = RichEditorImageToHTMLService(text)()

        # assert
        assert response == expected

    def test_call__parse_description__ok(self, mocker):

        # arrange
        mocker.patch(
            'pneumatic_backend.services.html_converter.'
            'RichEditorImageToHTMLService.style',
            new=''
        )
        text = (
            'Embedded image:\n'
            '![EucmaqmWQAkI3hR.jpg](https://storage.com/ "desc")'
        )
        expected = (
            'Embedded image:\n'
            '<img alt="EucmaqmWQAkI3hR.jpg" src="https://storage.com/"/>'
        )

        # act
        response = RichEditorImageToHTMLService(text)()

        # assert
        assert response == expected

    def test_call__link__skip(self, mocker):

        # arrange
        mocker.patch(
            'pneumatic_backend.services.html_converter.'
            'RichEditorImageToHTMLService.style',
            new=''
        )
        text = (
            '[name of link.webm](https://www.pneumatic.app/test.webm)'
        )
        expected = (
            '[name of link.webm](https://www.pneumatic.app/test.webm)'
        )

        # act
        response = RichEditorImageToHTMLService(text)()

        # assert
        assert response == expected


class TestRichEditorListToHTMLService:

    def test__call__skip_first_number__ok(self, mocker):

        # arrange
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLList'
            '.style',
            new=' style=""'
        )
        text = (
            'This paragraph:\n\n'
            '2. One\n'
            '3. Two\n'
            '4. Three'
        )
        expected = (
            'This paragraph:\n'
            '<ol style="">'
            '<li>One</li>'
            '<li>Two</li>'
            '<li>Three</li>'
            '</ol>\n'
        )

        # act
        response = RichEditorListToHTMLService(text)()

        # assert
        assert expected == response

    def test__call__not_bullet_list__ignore(self):

        # arrange
        text = (
            'This paragraph won\'t be converted '
            'because starting number is not 1. or -:\n\n'
            '* One\n'
            '* Two\n'
            '* Three'
        )
        expected = (
            'This paragraph won\'t be converted '
            'because starting number is not 1. or -:\n'
            '* One\n'
            '* Two\n'
            '* Three'
        )

        # act
        response = RichEditorListToHTMLService(text)()

        # assert
        assert expected == response

    def test__call__same_number__ok(self, mocker):

        # arrange
        text = (
            'This paragraph will be converted:\n'
            '1. One\n'
            '2. Two\n'
            '  - Two.one\n'
            '  - Two.two\n'
            '    1. Two.two.one\n'
            '    1. Two.two.two\n'
            '3. Three'
        )
        expected = (
            'This paragraph will be converted:\n'
            '<ol style="">'
            '<li>One</li>'
            '<li>Two<ul><li>Two.one</li>'
            '<li>Two.two<ol><li>Two.two.one</li>'
            '<li>Two.two.two</li>'
            '</ol></li></ul></li>'
            '<li>Three</li>'
            '</ol>\n'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLList'
            '.style',
            new=' style=""'
        )

        # act
        response = RichEditorListToHTMLService(text)()

        # assert
        assert expected == response

    def test__call__different_lists__join(self, mocker):

        """ Html not allow use different types of lists in the same level -
            - Join different lists in to one """

        # arrange
        text = (
            'This paragraph will be converted to bullets list:\n'
            '- One\n'
            '2. Two\n'
            '- Three\n'
            '  - Three.one\n'
            '  - Three.two\n'
            '    - Three.two.one\n'
            '    - Three.two.two\n'
            '  1. Three.three'
        )
        expected = (
            'This paragraph will be converted to bullets list:\n'
            '<ul style="">'
            '<li>One</li>'
            '<li>Two</li>'
            '<li>Three<ul>'
            '<li>Three.one</li><li>Three.two<ul>'
            '<li>Three.two.one</li><li>Three.two.two</li>'
            '</ul></li><li>Three.three</li></ul></li></ul>\n'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLList'
            '.style',
            new=' style=""'
        )

        # act
        response = RichEditorListToHTMLService(text)()

        # assert
        assert expected == response

    def test__call__broken__first_indent__skip(self, mocker):

        # arrange
        text = (
            'This paragraph will be converted to bullet list '
            'started from Three:\n'
            ' - One\n'
            '2. Two\n'
            '- Three\n'
        )
        expected = (
            'This paragraph will be converted to bullet list'
            ' started from Three:\n'
            ' - One\n'
            '<ol style=""><li>Two</li><li>Three</li></ol>\n'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLList'
            '.style',
            new=' style=""'
        )

        # act
        response = RichEditorListToHTMLService(text)()

        # assert
        assert expected == response


class TestRichEditorChecklistToHTMLService:

    def test__call__two_checklist_items__ok(self, mocker):

        # arrange
        text = (
            '[clist:cl-1|cli-1]First item[/clist]\n'
            '[clist:cl-1|cli-2]Second item[/clist]\n'
        )
        expected = (
            '<ol style="">'
            '<li>First item</li>'
            '<li>Second item</li>'
            '</ol>\n'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLParagraph'
            '.html_pattern',
            new='<p>{text}</p>'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLList'
            '.style',
            new=' style=""'
        )

        # act
        response = RichEditorChecklistToHTMLService(text)()

        # assert
        assert expected == response

    def test__call__two_checklists__ok(self, mocker):

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
            '<ol style="">'
            '<li>First item</li>'
            '<li>Second item</li>'
            '</ol>\n'
            'Text middle.\n'
            'Some text.\n'
            '<ol style="">'
            '<li>Third item</li>'
            '<li>Fourth item</li>'
            '</ol>\n'
            'Text after.'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLParagraph'
            '.html_pattern',
            new='<p>{text}</p>'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLList'
            '.style',
            new=' style=""'
        )

        # act
        response = RichEditorChecklistToHTMLService(text)()

        # assert
        assert expected == response

    def test__call__included_markup__ok(self, mocker):

        # arrange
        text = (
            '[clist:cl-1|cli-1]***First item***[/clist]\n'
            '[clist:cl-1|cli-2]**Second {{field-1}} item**[/clist]\n'
            '[clist:cl-1|cli-3][link](http://go.com) to site[/clist]\n'
        )
        expected = (
            '<ol style="">'
            '<li>***First item***</li>'
            '<li>**Second {{field-1}} item**</li>'
            '<li>[link](http://go.com) to site</li>'
            '</ol>\n'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLParagraph'
            '.html_pattern',
            new='<p>{text}</p>'
        )
        mocker.patch(
            'pneumatic_backend.services.html_converter.HTMLList'
            '.style',
            new=' style=""'
        )

        # act
        response = RichEditorChecklistToHTMLService(text)()

        # assert
        assert expected == response

    class TestRichEditorTableToHtmlService:

        def test__call__one_table__ok(self):
            # arrange
            text = (
                '| Heading 1 | Heading 2 |\n'
                '|---|---|\n'
                '| Line 1, cell 1 | Line 1, cell 2 |\n'
                '| Line 2, cell 1 | Line 2, cell 2 |\n\n'
            )
            expected = (
                '<table class="description-table">'
                '<tr>'
                '<th>Heading 1</th>'
                '<th>Heading 2</th>'
                '</tr>'
                '<tr>'
                '<td>Line 1, cell 1</td>'
                '<td>Line 1, cell 2</td>'
                '</tr>'
                '<tr>'
                '<td>Line 2, cell 1</td>'
                '<td>Line 2, cell 2</td>'
                '</tr>'
                '</table>\n'
            )

            # act
            response = RichEditorTableToHtmlService(text)()

            # assert
            assert expected == response

        def test__call__two_tables__ok(self):
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
                '<table class="description-table">'
                '<tr>'
                '<th>Heading 1</th>'
                '<th>Heading 2</th>'
                '</tr>'
                '<tr>'
                '<td>Line 1, cell 1</td>'
                '<td>Line 1, cell 2</td>'
                '</tr>'
                '<tr>'
                '<td>Line 2, cell 1</td>'
                '<td>Line 2, cell 2</td>'
                '</tr>'
                '</table>\n'
                '<table class="description-table">'
                '<tr>'
                '<th>Heading 3</th>'
                '<th>Heading 4</th>'
                '</tr>'
                '<tr>'
                '<td>Italics</td>'
                '<td>'
                '*Italics*</td>'
                '</tr>'
                '<tr>'
                '<td>Bold</td>'
                '<td>**Bold**</td>'
                '</tr>'
                '<tr>'
                '<td>Bold italics</td>'
                '<td>'
                '***Bold italics***</td>'
                '</tr>'
                '<tr>'
                '<td>link</td>'
                '<td>'
                '[Attach PO](https://storage.com/...tline.pdf)'
                '</td>'
                '</tr>'
                '</table>\n'
            )

            # act
            response = RichEditorTableToHtmlService(text)()

            # assert
            assert expected == response


def test_convert_text_to_html__mixed_markup__ok(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.services.html_converter.HTMLParagraph'
        '.html_pattern',
        new='<p>{text}</p>'
    )
    mocker.patch(
        'pneumatic_backend.services.html_converter.HTMLList'
        '.style',
        new=' style=""'
    )
    mocker.patch(
        'pneumatic_backend.services.html_converter.'
        'RichEditorImageToHTMLService.style',
        new=''
    )

    text = (
        'This paragraph will be converted to bullets list:\n'
        '- One\n'
        '2. Two\n'
        '- Three\n'
        '  - Three.one\n'
        '  - Three.two\n'
        '    - Three.two.one\n'
        '    - Three.two.two\n'
        '  1. Three.three\n'
        '![image](https://go.net/img.jpg)'
    )
    expected = (
        '<p>This paragraph will be converted to bullets list:</p>\n'
        '<ul style="">'
        '<li>One</li><li>Two</li><li>Three<ul>'
        '<li>Three.one</li><li>Three.two<ul>'
        '<li>Three.two.one</li><li>Three.two.two</li>'
        '</ul></li><li>Three.three</li></ul></li></ul><br/>\n'
        '<p><img alt="image" src="https://go.net/img.jpg"/></p><br/>\n<br/>\n'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test_convert_text_to_html__checklist__ok(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.services.html_converter.HTMLParagraph'
        '.html_pattern',
        new='<p>{text}</p>'
    )
    mocker.patch(
        'pneumatic_backend.services.html_converter.HTMLList'
        '.style',
        new=' style=""'
    )
    mocker.patch(
        'pneumatic_backend.services.html_converter.'
        'RichEditorImageToHTMLService.style',
        new=''
    )

    # arrange
    text = (
        'Text before.\n'
        '- One\n'
        '2. Two\n'
        '- Three\n'
        '  - Three.one\n'
        '  - Three.two\n'
        '    - Three.two.one\n'
        '    - Three.two.two\n'
        '  1. Three.three\n'
        'Checklist title:\n'
        '[clist:cl-1|cli-1]***First item***[/clist]\n'
        '[clist:cl-1|cli-2]**Second {{field-1}} item**[/clist]\n'
        '[clist:cl-1|cli-3][link](http://go.com) to site[/clist]\n'
        '![image](https://go.net/img.jpg)\n\n'
        '[clist:cl-2|cli-5]![image](http://go.com/img.jpg)[/clist]\n'
        'Text after.'
    )
    expected = (
        '<p>Text before.</p>\n'
        '<ul style="">'
        '<li>One</li><li>Two</li><li>Three<ul>'
        '<li>Three.one</li><li>Three.two<ul>'
        '<li>Three.two.one</li><li>Three.two.two</li>'
        '</ul></li><li>Three.three</li></ul></li></ul><br/>\n'
        '<p>Checklist title:</p>\n'
        '<ol style="">'
        '<li><em><b>First item</b></em></li>'
        '<li><b>Second {{field-1}} item</b></li>'
        '<li><a href="http://go.com">link</a> to site</li>'
        '</ol><br/>\n'
        '<p><img alt="image" src="https://go.net/img.jpg"/></p><br/>\n<br/>\n'
        '<ol style="">'
        '<li><img alt="image" src="http://go.com/img.jpg"/></li>'
        '</ol><br/>\n'
        '<p>Text after.</p>\n'
        '<br/>\n'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert response == expected


def test_convert_text_to_html__mixed_items__ok(mocker):

    # arrange
    mocker.patch(
        'pneumatic_backend.services.html_converter.HTMLParagraph'
        '.html_pattern',
        new='<p>{text}</p>'
    )
    mocker.patch(
        'pneumatic_backend.services.html_converter.HTMLList'
        '.style',
        new=' style=""'
    )
    mocker.patch(
        'pneumatic_backend.services.html_converter.'
        'RichEditorImageToHTMLService.style',
        new=''
    )
    text = (
        'Checklist title:\n'
        '[clist:cl-1|cli-1]The list, item 1[/clist]\n'
        '[clist:cl-1|cli-2]The list, item 2[/clist]\n'
        '*Italics*\n'
        '**Bold**\n'
        '***Bold italics***\n'
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
        '<ol style=""><li>The list, item 1</li><li>The list, item 2</li></ol>'
        '<br/>\n'
        '<p><em>Italics</em></p>\n'
        '<p><b>Bold</b></p>\n'
        '<p><em><b>Bold italics</b></em></p>\n'
        '<p><a href="https://storage.com/...tline.pdf">Attach PO</a></p>\n'
        '<table class="description-table">'
        '<tr>'
        '<th>Heading 1</th>'
        '<th>Heading 2</th>'
        '</tr>'
        '<tr>'
        '<td>Line 1, cell 1</td>'
        '<td>Line 1, cell 2</td>'
        '</tr>'
        '<tr>'
        '<td>Line 2, cell 1</td>'
        '<td>Line 2, cell 2</td>'
        '</tr>'
        '</table><br/>\n'
        '<p>The text after the table.</p>\n'
        '<table class="description-table">'
        '<tr>'
        '<th>Heading 3</th>'
        '<th>Heading 4</th>'
        '</tr>'
        '<tr>'
        '<td>Italics</td>'
        '<td><em>Italics</em></td>'
        '</tr>'
        '<tr>'
        '<td>Bold</td>'
        '<td><b>Bold</b></td>'
        '</tr>'
        '<tr>'
        '<td>Bold italics</td>'
        '<td>'
        '<em><b>Bold italics</b></em>'
        '</td>'
        '</tr>'
        '<tr>'
        '<td>link</td>'
        '<td>'
        '<a href="https://storage.com/...tline.pdf">Attach PO</a>'
        '</td>'
        '</tr>'
        '</table><br/>\n'
        '<p>The text after the table.</p>\n'
        '<br/>\n'
    )

    # act
    response = convert_text_to_html(text)

    # assert
    assert expected == response
