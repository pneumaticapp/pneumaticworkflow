import {
  ATTACHMENT_MARKDOWN_INLINE_RE,
  ATTACHMENT_MARKDOWN_LINE_RE,
  GENERAL_MARKDOWN_LINK_IMPORT_RE,
  GENERAL_MARKDOWN_LINK_RE,
  escapeMarkdownLinkText,
  parseAttachmentMarkdownFromStart,
  parseGeneralMarkdownLinkFromStart,
  unescapeMarkdownLinkText,
} from '../markdownLinkText';

describe('attachment markdown regex', () => {
  it('matches attachment with unescaped brackets in filename', () => {
    const markdown = '![report[Q1].pdf](https://example.com/f "entityType:file")';
    const match = ATTACHMENT_MARKDOWN_LINE_RE.exec(markdown);

    expect(match).not.toBeNull();
    expect(match?.[1]).toBe('report[Q1].pdf');
    expect(match?.[2]).toBe('https://example.com/f');
    expect(match?.[4]).toBe('file');
  });

  it('matches attachment with escaped brackets in filename', () => {
    const markdown = '![report\\[Q1\\].pdf](https://example.com/f "entityType:file")';
    const match = ATTACHMENT_MARKDOWN_INLINE_RE.exec(markdown);

    expect(match).not.toBeNull();
    expect(unescapeMarkdownLinkText(match?.[1] ?? '')).toBe('report[Q1].pdf');
  });

  it('does not match attachment markdown without closing parenthesis', () => {
    const markdown = '![alt](url "entityType:file"';
    const match = parseAttachmentMarkdownFromStart(markdown);

    expect(match).toBeNull();
  });

  it('matches only the first attachment when two are on the same line', () => {
    const markdown =
      '![a](url1 "entityType:file") ![b](url2 "entityType:file")';
    const firstMatch = parseAttachmentMarkdownFromStart(markdown);
    const secondMatch = parseAttachmentMarkdownFromStart(
      markdown.slice(firstMatch?.[0].length ?? 0).trimStart(),
    );

    expect(firstMatch?.[1]).toBe('a');
    expect(firstMatch?.[2]).toBe('url1');
    expect(secondMatch?.[1]).toBe('b');
    expect(secondMatch?.[2]).toBe('url2');
  });
});

describe('general markdown link regex', () => {
  it('matches link text with nested brackets', () => {
    const markdown = '[ewfer[ergerg]ergerg](http://localhost:8000/templates/edit/19755/)';
    const match = GENERAL_MARKDOWN_LINK_RE.exec(markdown);

    expect(match).not.toBeNull();
    expect(match?.[1]).toBe('ewfer[ergerg]ergerg');
    expect(match?.[2]).toBe('http://localhost:8000/templates/edit/19755/');
  });

  it('matches only the first link when two are on the same line', () => {
    const markdown = '[a](url1) [b](url2)';
    const firstMatch = parseGeneralMarkdownLinkFromStart(markdown);
    const secondMatch = parseGeneralMarkdownLinkFromStart(
      markdown.slice(firstMatch?.[0].length ?? 0).trimStart(),
    );

    expect(firstMatch?.[1]).toBe('a');
    expect(firstMatch?.[2]).toBe('url1');
    expect(secondMatch?.[1]).toBe('b');
    expect(secondMatch?.[2]).toBe('url2');
  });

  it('finds the first inline link inside surrounding text', () => {
    const markdown = 'see [a](url1) and [b](url2)';
    const match = GENERAL_MARKDOWN_LINK_IMPORT_RE.exec(markdown);

    expect(match?.index).toBe(4);
    expect(match?.[1]).toBe('a');
    expect(match?.[2]).toBe('url1');
  });

  it('supports String.match used by Lexical markdown import', () => {
    const markdown = 'hello [click here](https://example.com) world';
    const match = markdown.match(GENERAL_MARKDOWN_LINK_IMPORT_RE);

    expect(match?.index).toBe(6);
    expect(match?.[0]).toBe('[click here](https://example.com)');
    expect(match?.[1]).toBe('click here');
    expect(match?.[2]).toBe('https://example.com');
  });
});

describe('escapeMarkdownLinkText', () => {
  it('escapes ] in link text', () => {
    expect(escapeMarkdownLinkText('click [here]')).toBe('click [here\\]');
  });
});

describe('unescapeMarkdownLinkText', () => {
  it('returns plain text unchanged', () => {
    expect(unescapeMarkdownLinkText('report.pdf')).toBe('report.pdf');
  });

  it('unescapes ] in link alt text', () => {
    expect(unescapeMarkdownLinkText('report\\[Q1\\].pdf')).toBe('report[Q1].pdf');
  });

  it('unescapes backslashes', () => {
    expect(unescapeMarkdownLinkText('path\\\\to\\\\file')).toBe('path\\to\\file');
  });

  it('unescapes mixed brackets and backslashes', () => {
    expect(unescapeMarkdownLinkText('file\\[1\\].pdf')).toBe('file[1].pdf');
  });
});
