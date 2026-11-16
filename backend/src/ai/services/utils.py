from typing import Optional
from xml.sax.saxutils import escape


ATTR_ENTITIES = {'"': '&quot;'}


def escape_closing_tags(text: str) -> str:

    """ Neutralizes closing tags in a text written by a user,
        so that it cannot break a section boundary """

    return text.replace('</', '<\\/')


def as_tag(
    tag: str,
    content: Optional[str] = None,
    inline: bool = False,
    **attrs,
) -> str:

    """ XML tag with the attributes in the order they are given.
        A tag without content is rendered as a self closing one """

    rendered_attrs = ''.join(
        f' {key}="{escape(str(value), ATTR_ENTITIES)}"'
        for key, value in attrs.items()
    )
    if not content:
        return f'<{tag}{rendered_attrs}/>'
    if inline:
        return f'<{tag}{rendered_attrs}>{content}</{tag}>'
    return f'<{tag}{rendered_attrs}>\n{content}\n</{tag}>'
