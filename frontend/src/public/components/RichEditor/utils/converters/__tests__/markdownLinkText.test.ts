import {
  ATTACHMENT_MARKDOWN_INLINE_RE,
  ATTACHMENT_MARKDOWN_LINE_RE,
  GENERAL_MARKDOWN_LINK_RE,
  escapeMarkdownLinkText,
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
});

describe('general markdown link regex', () => {
  it('matches link text with nested brackets', () => {
    const markdown = '[ewfer[ergerg]ergerg](http://localhost:8000/templates/edit/19755/)';
    const match = GENERAL_MARKDOWN_LINK_RE.exec(markdown);

    expect(match).not.toBeNull();
    expect(match?.[1]).toBe('ewfer[ergerg]ergerg');
    expect(match?.[2]).toBe('http://localhost:8000/templates/edit/19755/');
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
