from abc import abstractmethod
from typing import Optional, Tuple, List
from pneumatic_backend.services.markdown import MarkdownPatterns


class HTMLParagraph:
    html_pattern = (
        '<p style="font-size:16px;'
        ' line-height: 19px; word-break: break-word;">'
        '{text}'
        '</p>'
    )

    def __init__(self, text):
        self._text = text

    def __str__(self):
        return self.html_pattern.format(text=self._text)


class HTMLList:
    html_tag = None
    style = (
        ' style="font-size:16px;'
        ' line-height: 19px; word-break: break-word;"'
    )

    def __init__(self, with_style: bool = False):
        self._is_open_li = False
        style = self.style if with_style else ''
        self._html = f'<{self.html_tag}{style}>'

    def append(self, item):
        self._is_open_li = True
        self._html += f'<li>{item}'

    def add_nested_list(self, nested):
        self._html += nested

    def close_li(self):
        if self._is_open_li:
            self._html += f'</li>'
            self._is_open_li = False

    def close(self):
        self.close_li()
        self._html += f'</{self.html_tag}>'

    def __str__(self):
        return self._html


class HTMLBulletsList(HTMLList):
    html_tag = 'ul'


class HTMLNumberedList(HTMLList):
    html_tag = 'ol'


class RichEditorToHTML:

    def __init__(self, text):
        self._text = text
        self._converted_text = ''

    @abstractmethod
    def _convert(self):
        pass

    def __call__(self):
        self._convert()
        return self._converted_text


class BaseListToHTML(RichEditorToHTML):

    @abstractmethod
    def _close_list(self, **kwargs):
        pass

    @abstractmethod
    def _process_list_item(self, **kwargs):
        pass

    @abstractmethod
    def _process_line(self, line: Optional[str] = None):
        pass


class RichEditorListToHTMLService(BaseListToHTML):

    LIST_PATTERN = MarkdownPatterns.LIST_PATTERN

    def __init__(self, text: str):
        super().__init__(text)
        self._stack_list: Optional[List[Tuple[int, HTMLList]]] = None

    def _close_list(self, depth: int = -1) -> str:
        if self._stack_list:
            current_depth, html = self._stack_list.pop()
            html.close()
            converted_list = str(html)
            while len(self._stack_list):
                current_depth, html = self._stack_list[-1]
                if current_depth <= depth:
                    return converted_list
                html.add_nested_list(converted_list)
                html.close()
                converted_list = str(html)
                self._stack_list.pop()
            return converted_list + '\n'  # after close top level list
        else:
            return ''

    def _create_nested_list(self, depth: int, label: str, text: str):
        if label == '-':
            nested_list = HTMLBulletsList()
        else:
            nested_list = HTMLNumberedList()
        nested_list.append(text)
        nested_item = (depth, nested_list)
        self._stack_list.append(nested_item)

    def _close_nested_lists(self, depth: int, text: str):
        list_text = self._close_list(depth=depth)
        if self._stack_list:
            _, current_list = self._stack_list[-1]
            current_list.add_nested_list(list_text)
            self._enrich_current_list(current_list=current_list, text=text)
            self._stack_list[-1] = (depth, current_list)
        else:
            self._converted_text += list_text

    def _enrich_current_list(self, current_list: HTMLList, text: str):
        current_list.close_li()
        current_list.append(text)

    def _process_list_item(
        self,
        new_depth: int,
        label: str,
        text: str,
        is_bullets: bool
    ):
        if self._stack_list:
            current_depth, current_list = self._stack_list[-1]
            if current_depth == new_depth:
                self._enrich_current_list(
                    current_list=current_list,
                    text=text
                )
            elif current_depth < new_depth:
                self._create_nested_list(
                    depth=new_depth,
                    label=label,
                    text=text
                )
            elif current_depth > new_depth and len(self._stack_list) > 1:
                self._close_nested_lists(
                    depth=new_depth,
                    text=text
                )
        else:
            current_list = (
                HTMLBulletsList(with_style=True)
                if is_bullets else
                HTMLNumberedList(with_style=True)
            )
            current_list.append(text)
            self._stack_list = [(new_depth, current_list)]

    def _is_numeric(self, depth: int, label: str):

        is_numeric = False
        if not label.startswith('-'):
            if depth != 0 and not self._stack_list:
                is_numeric = False
            else:
                is_numeric = True
        return is_numeric

    def is_bullets(self, depth: int, label: str):
        is_bullets = False
        if label.startswith('-'):
            if depth != 0 and not self._stack_list:
                is_bullets = False
            else:
                is_bullets = True
        return is_bullets

    def _process_line(self, line: Optional[str] = None):
        match = self.LIST_PATTERN.match(line)
        if match:
            label = match.group('label')
            depth = len(match.group('depth'))
            text = match.group('text').strip()
            is_bullets = self.is_bullets(depth=depth, label=label)
            if is_bullets or self._is_numeric(depth=depth, label=label):
                self._process_list_item(
                    new_depth=depth,
                    label=label,
                    text=text,
                    is_bullets=is_bullets
                )
                return
        self._converted_text += self._close_list()
        if line.strip():
            self._converted_text += line

    def _convert(self):

        for line in self._text.splitlines(True):
            self._process_line(line)

        if self._stack_list:
            self._converted_text += self._close_list()


class RichEditorImageToHTMLService(RichEditorToHTML):

    IMAGE_MARKDOWN_PATTERN = MarkdownPatterns.IMAGE_MARKDOWN_PATTERN
    style = (
        ' style="margin: 0 auto; display: block;'
        ' width: auto; max-height: 320px; max-width: 590px;"'
    )
    IMAGE_HTML = '<img alt="{name}" src="{link}"{style}/>'

    def _convert(self):
        self._converted_text = self._text
        images = self.IMAGE_MARKDOWN_PATTERN.finditer(self._text)
        for image in images:
            name = image.group('name')
            link = image.group('link')
            description = image.group('desc') or ''
            self._converted_text = self._converted_text.replace(
                f'![{name}]({link}{description})',
                self.IMAGE_HTML.format(
                    name=name,
                    link=link,
                    style=self.style
                )
            )


class RichEditorBoldToHTMLService(RichEditorToHTML):

    BOLD_PATTERN = MarkdownPatterns.BOLD_PATTERN
    BOLD_HTML = '<b>{text}</b>'

    def _convert(self):
        self._converted_text = self._text
        bolds = self.BOLD_PATTERN.finditer(self._text)
        for bold in bolds:
            text = bold.groups()[0]
            self._converted_text = self._converted_text.replace(
                f'**{text}**',
                self.BOLD_HTML.format(text=text)
            )


class RichEditorItalicToHTMLService(RichEditorToHTML):

    ITALIC_PATTERN = MarkdownPatterns.ITALIC_PATTERN
    ITALIC_HTML = '<em>{text}</em>'

    def _convert(self):
        self._converted_text = self._text
        italics = self.ITALIC_PATTERN.finditer(self._text)
        for italic in italics:
            text = italic.groups()[0]
            self._converted_text = self._converted_text.replace(
                f'*{text}*',
                self.ITALIC_HTML.format(text=text)
            )


class RichEditorNewlineToHTMLService(RichEditorToHTML):

    def _convert(self):
        for line in self._text.splitlines():
            if line.startswith(('<ul', '<ol')):
                self._converted_text += (line + '<br/>\n')
            elif line.startswith('<img'):
                self._converted_text += (
                    str(HTMLParagraph(line)) + '<br/>\n<br/>\n'
                )
            elif line.startswith('<table'):
                self._converted_text += line + '<br/>\n'
            elif line:
                self._converted_text += (str(HTMLParagraph(line)) + '\n')
        if not self._converted_text.endswith('<br/>\n'):
            self._converted_text += '<br/>\n'


class RichEditorTableToHtmlService(RichEditorToHTML):

    TABLE_HTML = '<table class="description-table">{rows}</table>'
    TABLE_THEAD_CELL_HTML = '<th>{text}</th>'
    TABLE_ROW_HTML = '<tr>{cells}</tr>'
    TABLE_CELL_HTML = '<td>{text}</td>'

    def _convert(self):
        self._converted_text = self._text
        tables = MarkdownPatterns.TABLE_MARKDOWN_PATTERN.finditer(self._text)
        for table in tables:
            lines = ''.join(table.groups())
            table_html = self._convert_table(table)
            self._converted_text = self._converted_text.replace(
                lines,
                table_html
            )

    def _convert_table(self, table):
        table_html = ''
        thead = table.group('thead')
        thead_row_html = ''.join(
            self.TABLE_THEAD_CELL_HTML.format(text=cell.strip())
            for cell in thead.split('|')[1:-1]
        )
        table_html += self.TABLE_ROW_HTML.format(cells=thead_row_html)
        tbody = table.group('tbody')
        tbody_rows = tbody.strip().split('\n')
        for tbody_row in tbody_rows:
            tbody_row_html = ''.join(
                self.TABLE_CELL_HTML.format(text=cell.strip())
                for cell in tbody_row.split('|')[1:-1]
            )
            table_html += self.TABLE_ROW_HTML.format(cells=tbody_row_html)
        return self.TABLE_HTML.format(rows=table_html)


class RichEditorLinkToHtmlService(RichEditorToHTML):

    LINK_MARKDOWN_PATTERN = MarkdownPatterns.LINK_MARKDOWN_PATTERN
    LINK_HTML = '<a href="{link}">{name}</a>'

    def _convert(self):
        self._converted_text = self._text
        images = self.LINK_MARKDOWN_PATTERN.finditer(self._text)
        for image in images:
            name = image.group('name')
            link = image.group('link')
            description = image.group('desc') or ''
            self._converted_text = self._converted_text.replace(
                f'[{name}]({link}{description})',
                self.LINK_HTML.format(name=name, link=link)
            )


class RichEditorChecklistToHTMLService(BaseListToHTML):

    CHECKLIST_ITEM_PATTERN = MarkdownPatterns.CHECKLIST_ITEM_PATTERN

    def __init__(self, text: str):
        super().__init__(text)
        self._current_list: Optional[HTMLNumberedList] = None

    def _close_list(self, **kwargs) -> str:
        if self._current_list:
            self._current_list.close()
            html_str = str(self._current_list)
            self._current_list = None
            return html_str + '\n'
        else:
            return ''

    def _process_list_item(self, list_item: str):
        if self._current_list is None:
            self._current_list = HTMLNumberedList(with_style=True)
        self._current_list.append(list_item)
        self._current_list.close_li()

    def _process_line(self, line: Optional[str] = None):
        match = self.CHECKLIST_ITEM_PATTERN.match(line.strip())
        if match:
            self._process_list_item(list_item=match.group('text'))
        else:
            self._converted_text += self._close_list()
            if line:
                self._converted_text += line

    def _convert(self):
        for line in self._text.splitlines(True):
            self._process_line(line)
        if self._current_list:
            self._converted_text += self._close_list()


def convert_text_to_html(text: str) -> str:
    text = RichEditorTableToHtmlService(text)()
    text = RichEditorBoldToHTMLService(text)()
    text = RichEditorItalicToHTMLService(text)()
    text = RichEditorImageToHTMLService(text)()
    text = RichEditorLinkToHtmlService(text)()
    text = RichEditorListToHTMLService(text)()
    text = RichEditorChecklistToHTMLService(text)()
    text = RichEditorNewlineToHTMLService(text)()
    return text
