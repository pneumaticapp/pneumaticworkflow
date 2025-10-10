# pylint:disable=anomalous-backslash-in-string
from abc import abstractmethod
from typing import Optional
from src.services.markdown import MarkdownPatterns
from markdown import markdown
import re


list_block_pattern = re.compile(
    pattern=r'(^(?:\s*(?:(?:\d+\.)|[\-\+\*])\s+.*?(?:\n|$))+)',
    flags=re.M
)

table_block_pattern = re.compile(
    pattern=r'(^(?:\|[^\n]+\|\r?\n)+)',
    flags=re.M
)
paragraph_block_pattern = re.compile(
    pattern=r'^(?P<paragraph>(?:([*_`]|\*\*|\[){0,1}[a-zA-Z]+)(.*))',
    flags=re.M
)


class HTMLList:
    html_tag = None

    def __init__(self):
        self._is_open_li = False
        self._html = f'<{self.html_tag}>'

    def append(self, item):
        self._is_open_li = True
        self._html += f'<li>{item}'

    def add_nested_list(self, nested):
        self._html += nested

    def close_li(self):
        if self._is_open_li:
            self._html += '</li>'
            self._is_open_li = False

    def close(self):
        self.close_li()
        self._html += f'</{self.html_tag}>'

    def __str__(self):
        return self._html


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


class RichEditorChecklistToHTMLService(BaseListToHTML):
    CHECKLIST_ITEM_PATTERN = MarkdownPatterns.CHECKLIST_ITEM_PATTERN

    def __init__(self, text: str):
        super().__init__(text)
        self._current_list: Optional[HTMLNumberedList] = None

    @staticmethod
    def _no_p_html(string: str) -> str:
        return re.sub("(^<P>|</P>$)", "", markdown(string),
                      flags=re.IGNORECASE)

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
            self._current_list = HTMLNumberedList()
        self._current_list.append(self._no_p_html(list_item))
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


def _normalize_markdown_blocks(text: str) -> str:

    """
    Normalizes Markdown by adding two line breaks
    for proper HTML conversion by the markdown library:
    - before and after tables
    - before and after lists
    - after each new line of text to convert to a paragraph
    """

    def normalize_block(match: re.Match, text: str) -> str:
        block = match.group(0).rstrip('\n')
        start, end = match.start(), match.end()
        before = '\n\n' if start > 0 and text[start - 1] != '\n' else '\n'
        after = '\n\n' if end < len(text) and text[end] != '\n' else '\n'
        return f"{before}{block}{after}"

    text = list_block_pattern.sub(lambda m: normalize_block(m, text), text)
    text = table_block_pattern.sub(lambda m: normalize_block(m, text), text)
    text = paragraph_block_pattern.sub('\g<paragraph>\n\n', text)

    return re.sub(r'\n{3,}', '\n\n', text).strip('\n')


def convert_text_to_html(text: str) -> str:
    text = RichEditorChecklistToHTMLService(text)()

    # TODO delete it when fix editor on frontend
    text = _normalize_markdown_blocks(text)

    text = markdown(text, extensions=['tables'])
    return text
