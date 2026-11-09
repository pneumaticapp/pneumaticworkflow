import * as React from 'react';
import { render } from '@testing-library/react';

import { RichText } from '../RichText';
import { sanitizeRichTextHtml } from '../utils/sanitizeRichTextHtml';
import { EExtraFieldType } from '../../../types/template';
import styles from '../RichText.css';

describe('RichText content direction', () => {
  it('lets each prose paragraph and heading determine its own direction', () => {
    const text = 'طلب إسكان جديد\n\nReview the attachments\n\n## تفاصيل الطلب';
    const { container } = render(<RichText text={text} />);

    expect(Array.from(container.querySelectorAll('p, h2')).map((element) => element.getAttribute('dir'))).toEqual([
      'auto', 'auto', 'auto',
    ]);
    expect(container.textContent).toContain('طلب إسكان جديد');
    expect(container.textContent).toContain('Review the attachments');
    // Structural containers continue to inherit the active UI direction.
    expect(container.firstElementChild?.hasAttribute('dir')).toBe(false);
    expect(text).toBe('طلب إسكان جديد\n\nReview the attachments\n\n## تفاصيل الطلب');
  });

  it('keeps a loose list marker and its first paragraph in the same direction', () => {
    const text = '- مراجعة الطلب\n\n  Review supporting documents\n\n- Approve the request\n\n  إرسال الإشعار';
    const { container } = render(<RichText text={text} />);
    const items = container.querySelectorAll('li');

    expect(items).toHaveLength(2);
    items.forEach((item) => {
      expect(item.getAttribute('dir')).toBe('auto');
      const paragraphs = item.querySelectorAll('p');
      // Giving both elements dir=auto would hide the first paragraph from its li.
      expect(paragraphs[0].hasAttribute('dir')).toBe(false);
      expect(paragraphs[1].getAttribute('dir')).toBe('auto');
    });
    expect(container.querySelector('ul')?.hasAttribute('dir')).toBe(false);
  });

  it('keeps ordered/nested lists and checklist IDs while directing individual items', () => {
    const text = [
      '1. Review the request',
      '   - مراجعة الوثائق',
      '2. إرسال الموافقة',
      '',
      '[clist:approval-list|review]مراجعة الطلب[/clist]',
      '[clist:approval-list|send]Send the notification[/clist]',
    ].join('\n');
    const { container } = render(<RichText text={text} interactiveChecklists />);

    expect(container.querySelectorAll('li[dir="auto"]')).toHaveLength(3);
    const checklists = container.querySelectorAll(`.${styles['checklist__item']}`);
    expect(checklists).toHaveLength(2);
    checklists.forEach((item) => expect(item.getAttribute('dir')).toBe('auto'));
    expect(container.querySelector('[id*="approval-list"]')).not.toBeNull();
    expect(container.textContent).toContain('Send the notification');
  });

  it('isolates technical values while keeping inline Arabic labels visible to native paragraph direction', () => {
    const text = 'مراجعة [سامر عجاج|42] و{{client}} عبر [تفاصيل الطلب](https://example.com/request) أو https://example.com/a?b=1&c=2، ثم `request_id=42`';
    const { container } = render(
      <RichText
        text={text}
        embedVideos={false}
        variables={[{ apiName: 'client', title: 'اسم مقدم الطلب', type: EExtraFieldType.String }]}
      />,
    );
    const namedLink = container.querySelector('a[href="https://example.com/request"]');
    const url = container.querySelector('a[href^="https://example.com/a"]');
    const mention = container.querySelector(`.${styles.mention}`);
    const variable = container.querySelector(`.${styles['bidi-isolate']}`);

    expect(namedLink?.textContent).toBe('تفاصيل الطلب');
    expect(namedLink?.hasAttribute('dir')).toBe(false);
    expect(mention?.textContent).toBe('@سامر عجاج');
    expect(mention?.hasAttribute('dir')).toBe(false);
    expect(variable?.textContent).toBe('اسم مقدم الطلب');
    expect(variable?.hasAttribute('dir')).toBe(false);
    expect(url?.getAttribute('dir')).toBe('ltr');
    expect(container.querySelector('code')?.getAttribute('dir')).toBe('ltr');
    expect(container.querySelector('code')?.textContent).toBe('request_id=42');
  });

  it('directs plain-text renderings without parsing user HTML', () => {
    const { container } = render(<RichText text={'طلب جديد <strong>Review</strong> [سامر عجاج|42]'} isMarkdownMode={false} />);

    expect(container.firstElementChild?.getAttribute('dir')).toBe('auto');
    expect(container.querySelector('strong')).toBeNull();
    expect(container.textContent).toContain('<strong>Review</strong>');
    expect(container.textContent).toContain('@سامر عجاج');
  });

  it('preserves explicit authored direction and sanitizes HTML before decorating it', () => {
    const html = sanitizeRichTextHtml('<p dir="rtl" onclick="alert(1)">طلب <bdi>ABC-42</bdi></p><script>alert(1)</script><pre><code>if (a &lt; b) run();</code></pre>');
    const container = document.createElement('div');
    container.innerHTML = html;

    expect(container.querySelector('p')?.getAttribute('dir')).toBe('rtl');
    expect(container.querySelector('p')?.hasAttribute('onclick')).toBe(false);
    expect(container.querySelector('bdi')?.textContent).toBe('ABC-42');
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('pre')?.getAttribute('dir')).toBe('ltr');
    expect(container.querySelector('code')?.textContent).toBe('if (a < b) run();');
  });

  it('lets a list item see a leading heading or blockquote and respects an authored paragraph direction', () => {
    const html = sanitizeRichTextHtml('<ul><li><h3>تفاصيل الطلب</h3><p>Review the request</p></li><li><blockquote><p>إرسال الإشعار</p></blockquote></li><li><p dir="rtl">Request SY-42</p></li></ul>');
    const container = document.createElement('div');
    container.innerHTML = html;
    const items = container.querySelectorAll('li');

    expect(items[0].getAttribute('dir')).toBe('auto');
    expect(items[0].querySelector('h3')?.hasAttribute('dir')).toBe(false);
    expect(items[0].querySelector('p')?.getAttribute('dir')).toBe('auto');
    expect(items[1].querySelector('p')?.hasAttribute('dir')).toBe(false);
    expect(items[2].getAttribute('dir')).toBe('rtl');
    expect(items[2].querySelector('p')?.getAttribute('dir')).toBe('rtl');
  });
});
