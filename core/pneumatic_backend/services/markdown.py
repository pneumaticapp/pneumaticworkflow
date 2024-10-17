import re


class MarkdownPatterns:

    MENTION_PATTERN = re.compile(
        r'\[(?P<name>[^]]+)\|(?P<user_id>\d+)\]'
    )
    BOLD_PATTERN = re.compile(
        r'(?ms)\*{2}((?=[^\*\r\n]).*?[^\*\r\n])\*{2}'
    )
    ITALIC_PATTERN = re.compile(
        r'(?ms)\*((?=[^\*\r\n]).*?[^\*\r\n])\*'
    )
    LINK_MARKDOWN_PATTERN = re.compile(
        r'\[(?P<name>[^\]]+)\]\((?P<link>.*?)(?P<desc>\s*"(?:.*[^"])"\s*)?\)'
    )
    CHECKLIST_ITEM_PATTERN = re.compile(
        r'\[clist:(?:[\w-]+)\|(?:[\w-]+)\](?P<text>.*)\[\/clist]',
        flags=re.M
    )
    IMAGE_MARKDOWN_PATTERN = re.compile(
        r'!\[(?P<name>(?:[^\]].+))\]'
        r'\((?P<link>.*?)(?P<desc>\s*"(?:.*[^"])"\s*)?\)'
    )

    LIST_PATTERN = re.compile(
        r'^(?P<depth>\s*)(?P<label>(?:\d+\.)|(?:\-))(?P<text>.*)$',
        flags=re.M
    )

    TABLE_MARKDOWN_PATTERN = re.compile(
        r'(?ms)^(?P<thead>\|[^\n]+\|\r?\n)'
        r'(?P<delimiter>(?:\|:?[-]+:?)+\|)'
        r'(?P<tbody>\n(?:\|[^\n]+\|\r?\n?)*)?$'
    )


class MarkdownService:

    @classmethod
    def _clear_bold(cls, text: str) -> str:
        for bold in MarkdownPatterns.BOLD_PATTERN.finditer(text):
            clear = bold.groups()[0]
            text = text.replace(f'**{clear}**', clear)
        return text

    @classmethod
    def _clear_italic(cls, text: str) -> str:
        for italic in MarkdownPatterns.ITALIC_PATTERN.finditer(text):
            clear = italic.groups()[0]
            text = text.replace(f'*{clear}*', clear)
        return text

    @classmethod
    def _clear_images(cls, text: str) -> str:
        for image in MarkdownPatterns.IMAGE_MARKDOWN_PATTERN.finditer(text):
            name = image.group('name')
            url = image.group('link')
            description = image.group('desc') or ''
            text = text.replace(f'![{name}]({url}{description})', name)
        return text

    @classmethod
    def _clear_links(cls, text: str) -> str:
        for link in MarkdownPatterns.LINK_MARKDOWN_PATTERN.finditer(text):
            name = link.group('name')
            url = link.group('link')
            description = link.group('desc') or ''
            text = text.replace(f'[{name}]({url}{description})', name)
        return text

    @classmethod
    def _clear_list(cls, text: str) -> str:
        current_list = []
        lines = []
        for line in text.splitlines(True):
            match = (
                MarkdownPatterns.LIST_PATTERN.match(line) or
                MarkdownPatterns.CHECKLIST_ITEM_PATTERN.match(line.strip())
            )
            if match:
                text = match.group('text').strip()
                current_list.append(text)
            else:
                if current_list:
                    closed_list = ', '.join(current_list) + '\n'
                    current_list = []
                    lines.append(closed_list)
                lines.append(line)
        if current_list:
            closed_list = ', '.join(current_list)
            lines.append(closed_list)
        return ''.join(lines)

    @classmethod
    def _clear_mentions(cls, text: str) -> str:
        for mention in MarkdownPatterns.MENTION_PATTERN.finditer(text):
            name = mention.group('name')
            user_id = mention.group('user_id')
            text = text.replace(f'[{name}|{user_id}]', name)
        return text

    @classmethod
    def _clear_table(cls, text: str) -> str:
        for table in MarkdownPatterns.TABLE_MARKDOWN_PATTERN.finditer(text):
            lines = ''.join(table.groups())
            name = 'Таблица'
            text = text.replace(lines, name)
        return text

    @classmethod
    def clear(cls, text: str) -> str:
        if not text:
            return text
        return cls._clear_list(
            cls._clear_links(
                cls._clear_images(
                    cls._clear_italic(
                        cls._clear_bold(
                            cls._clear_mentions(
                                cls. _clear_table(text)
                            )
                        )
                    )
                )
            )
        )
