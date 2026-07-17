import * as React from 'react';
import { render } from '@testing-library/react';
import { RichText } from '../RichText';
import type { IRichTextProps } from '../types';

jest.mock('react-dom/server', () => ({
  __esModule: true,
  default: {
    renderToStaticMarkup: jest.fn((element: React.ReactElement) => {
      const props = element?.props as { name?: string; src?: string };
      if (props?.name) {
        return `<span>${props.name}</span>`;
      }
      if (props?.src) {
        return `<video src="${props.src}" />`;
      }
      return '<mock />';
    }),
  },
}));
import { intlMock } from '../../../__stubs__/intlMock';
import { EExtraFieldType } from '../../../types/template';
import { TTaskVariable } from '../../TemplateEdit/types';
import {
  WORKFLOW_STARTER_VARIABLE_API_NAME,
  WORKFLOW_STARTER_VARIABLE_TITLE,
} from '../../TemplateEdit/TaskForm/utils/getTaskVariables';

describe('RichText', () => {
  const LOCALIZED_WF_STARTER_TITLE = intlMock.formatMessage({ id: 'kickoff.system-varibale-workflow-starter' });

  it('renders multiple paragraphs without empty nbsp blocks', () => {
    const props: IRichTextProps = {
      text: 'Paragraph 1\n\nParagraph 2\n\n## Heading\n\nText below',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.querySelectorAll('p')).toHaveLength(3);
    expect(container.innerHTML).not.toContain('&nbsp;');
    expect(container.textContent).toContain('Paragraph 1');
    expect(container.textContent).toContain('Paragraph 2');
    expect(container.textContent).toContain('Heading');
    expect(container.textContent).toContain('Text below');
  });

  it('renders correct html for mentions and links', () => {
    const props: IRichTextProps = {
      text: 'Hello, [Jyoti Puri|3], look here: link: http://pneumatic.app/',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders mentions in different languages correctly', () => {
    const users = [
      { name: 'Alex Karpov-Konstantinov', id: 4 },
      { name: 'אלכסיי קרפוב-קונסטנטינוב', id: 5 },
      { name: 'アレクセイカルポフ-コンスタンティノフ', id: 6 },
    ];
    const usersString = users.map(({ name, id }) => `[${name}|${id}]`).join(', ');
    const props: IRichTextProps = {
      text: `Hello, ${usersString}`,
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const text = container.textContent ?? '';

    for (const user of users) {
      expect(text).toContain(`@${user.name}`);
    }
  });

  it('renders correct html for plain text', () => {
    const props: IRichTextProps = {
      text: 'Some plain text',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders single line breaks in markdown mode', () => {
    const props: IRichTextProps = {
      text: 'Line 1\nLine 2',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.querySelector('br')).not.toBeNull();
    expect(container.textContent).toContain('Line 1');
    expect(container.textContent).toContain('Line 2');
  });

  it('does not append trailing space to paragraphs separated by blank lines', () => {
    const props: IRichTextProps = {
      text: 'Paragraph one\n\nParagraph two\n\n',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const paragraphs = container.querySelectorAll('p');

    expect(paragraphs).toHaveLength(2);
    expect(paragraphs[0].textContent).toBe('Paragraph one');
    expect(paragraphs[1].textContent).toBe('Paragraph two');
    expect(container.innerHTML).not.toContain('&nbsp;');
  });

  it('clears xss', () => {
    const props: IRichTextProps = {
      text: '<script>console.log("I\'ll try to hack you")</script>',
      isMarkdownMode: false,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.querySelector('script')).toBeNull();
    expect(container.innerHTML).not.toMatch(/<script/i);
  });

  it('escapes raw HTML in non-markdown mode', () => {
    const props: IRichTextProps = {
      text: '<a href="https://phish.example">Approve</a>',
      isMarkdownMode: false,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.querySelector('a')).toBeNull();
    expect(container.textContent).toContain('<a href="https://phish.example">Approve</a>');
  });

  it('keeps stable hook order when text changes from empty to non-empty', () => {
    const props: IRichTextProps = { text: null, isMarkdownMode: true };
    const { container, rerender } = render(<RichText {...props} />);

    expect(container.firstChild).toBeNull();

    rerender(<RichText text="Loaded content" isMarkdownMode />);

    expect(container.textContent).toContain('Loaded content');
  });

  it('empty render if text prop is null', () => {
    const props: IRichTextProps = { text: null, isMarkdownMode: true };

    const { container } = render(<RichText {...props} />);

    expect(container.firstChild).toBeNull();
  });

  it('RichText and youtube in text flag return text with youtube iframe', () => {
    const props: IRichTextProps = {
      text: 'test1 https://www.youtube.com/watch?v=jNQXAC9IVRw',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const iframe = container.querySelector('iframe');

    expect(iframe?.getAttribute('src')).toBe('//www.youtube.com/embed/jNQXAC9IVRw');
    expect(container.firstChild).toMatchSnapshot();
  });

  it('RichText and loom link in text flag return text with loom iframe', () => {
    const props: IRichTextProps = {
      text: 'test1 https://www.loom.com/share/7f68fa7f01e349cab91b0c36168f68c3?t=1',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const iframe = container.querySelector('iframe');

    expect(iframe?.getAttribute('src')).toBe('https://www.useloom.com/embed/7f68fa7f01e349cab91b0c36168f68c3');
    expect(container.firstChild).toMatchSnapshot();
  });

  it('RichText and youtube and loom link in text flag return text with youtube and loom iframe', () => {
    const props: IRichTextProps = {
      text: 'test1 https://www.loom.com/share/7f68fa7f01e349cab91b0c36168f68c3?t=1 https://www.youtube.com/watch?v=jNQXAC9IVRw',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const iframes = container.querySelectorAll('iframe');

    expect(iframes[0]?.getAttribute('src')).toBe('https://www.useloom.com/embed/7f68fa7f01e349cab91b0c36168f68c3');
    expect(iframes[1]?.getAttribute('src')).toBe('//www.youtube.com/embed/jNQXAC9IVRw');
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders localized title in badge for system variable (workflow-starter)', () => {
    const variables: TTaskVariable[] = [
      {
        apiName: WORKFLOW_STARTER_VARIABLE_API_NAME,
        title: WORKFLOW_STARTER_VARIABLE_TITLE,
        type: EExtraFieldType.String,
      },
    ];

    const props: IRichTextProps = {
      text: 'Started by: {{workflow-starter}}',
      isMarkdownMode: false,
      variables,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.textContent).toContain(LOCALIZED_WF_STARTER_TITLE);
    expect(container.textContent).not.toContain('{{workflow-starter}}');
  });

  it('renders mention with ] in display name', () => {
    const props: IRichTextProps = {
      text: 'Reviewer: [John\\] Doe|42].',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.textContent).toContain('@John] Doe');
  });

  it('renders original title in badge for regular variable', () => {
    const variables: TTaskVariable[] = [
      {
        apiName: 'client-name-3967',
        title: 'Client name',
        type: EExtraFieldType.String,
      },
    ];

    const props: IRichTextProps = {
      text: 'Client: {{client-name-3967}}',
      isMarkdownMode: false,
      variables,
    };

    const { container } = render(<RichText {...props} />);
    expect(container.textContent).toContain('Client name');
    expect(container.textContent).not.toContain('{{client-name-3967}}');
  });

  it('renders file attachment with ] in filename', () => {
    const props: IRichTextProps = {
      text: '![report\\[Q1\\].pdf](https://example.com/f "entityType:file")',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.textContent).toContain('report[Q1].pdf');
    expect(container.innerHTML).not.toContain('![report');
  });

  it('renders file attachment with unescaped brackets in filename', () => {
    const props: IRichTextProps = {
      text: '![report[Q1].pdf](https://example.com/f "entityType:file")',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.textContent).toContain('report[Q1].pdf');
    expect(container.innerHTML).not.toContain('![report');
  });

  it('renders file attachment with [ and ] in filename', () => {
    const props: IRichTextProps = {
      text: '![file\\[1\\].pdf](https://example.com/f "entityType:file")',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.textContent).toContain('file[1].pdf');
    expect(container.innerHTML).not.toContain('![file');
  });

  it('renders regular link with ] in link text', () => {
    const props: IRichTextProps = {
      text: '[click \\[here\\]](https://example.com)',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const link = container.querySelector('a[href="https://example.com"]');

    expect(link).not.toBeNull();
    expect(link?.textContent).toBe('click [here]');
    expect(container.innerHTML).not.toContain('[click \\[here\\]]');
  });

  it('renders regular link with nested brackets in link text', () => {
    const props: IRichTextProps = {
      text: '[ewfer[ergerg]ergerg](http://localhost:8000/templates/edit/19755/)',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const link = container.querySelector('a[href="http://localhost:8000/templates/edit/19755/"]');

    expect(link).not.toBeNull();
    expect(link?.textContent).toBe('ewfer[ergerg]ergerg');
    expect(container.innerHTML).not.toContain('[ewfer[ergerg]');
  });

  it('does not treat markdown links as mentions when followed by a real mention', () => {
    const props: IRichTextProps = {
      text: 'Final: [help link](https://pneumatic.app/help), variable {{client-name-3967}}, mention [Support Team|12].',
      isMarkdownMode: true,
      variables: [
        {
          apiName: 'client-name-3967',
          title: 'Client name',
          type: EExtraFieldType.String,
        },
      ],
    };

    const { container } = render(<RichText {...props} />);
    const helpLink = container.querySelector('a[href="https://pneumatic.app/help"]');

    expect(helpLink).not.toBeNull();
    expect(helpLink?.textContent).toBe('help link');
    expect(container.textContent).toContain('@Support Team');
    expect(container.innerHTML).not.toContain('@help link');
  });

  it('renders image attachment with ] in alt text', () => {
    const props: IRichTextProps = {
      text: '![img\\[v2\\]](https://example.com/img.png "entityType:image")',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const image = container.querySelector('img[src="https://example.com/img.png"]');

    expect(image).not.toBeNull();
    expect(container.innerHTML).not.toContain('![img');
  });

  it('renders standard markdown image without entityType as img preview', () => {
    const props: IRichTextProps = {
      text: '![Architecture diagram](https://picsum.photos/400/200)',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);
    const image = container.querySelector('img[src="https://picsum.photos/400/200"]');
    const link = container.querySelector('a[href="https://picsum.photos/400/200"]');

    expect(image).not.toBeNull();
    expect(link).toBeNull();
    expect(container.innerHTML).not.toContain('![Architecture diagram');
  });

  it('renders markdown image with entityType file as document attachment', () => {
    const props: IRichTextProps = {
      text: '![report.pdf](https://example.com/report.pdf "entityType:file")',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.querySelector('img')).toBeNull();
    expect(container.textContent).toContain('report.pdf');
  });

  it('renders markdown image syntax with file extension as document attachment', () => {
    const props: IRichTextProps = {
      text: '![report.pdf](https://example.com/report.pdf)',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.querySelector('img')).toBeNull();
    expect(container.textContent).toContain('report.pdf');
  });

  describe('file-service URLs (no extension in URL)', () => {
    const FILE_SERVICE_URL = 'https://app.pneumatic.app/files';

    it('renders image as <img> when filename has image extension (.png)', () => {
      const props: IRichTextProps = {
        text: `[screenshot.png](${FILE_SERVICE_URL}/abc-123)`,
        isMarkdownMode: true,
      };

      const { container } = render(<RichText {...props} />);
      const image = container.querySelector(`img[src="${FILE_SERVICE_URL}/abc-123"]`);

      expect(image).not.toBeNull();
    });

    it('renders image as <img> when filename has .jpg extension', () => {
      const props: IRichTextProps = {
        text: `[photo.jpg](${FILE_SERVICE_URL}/def-456)`,
        isMarkdownMode: true,
      };

      const { container } = render(<RichText {...props} />);
      const image = container.querySelector(`img[src="${FILE_SERVICE_URL}/def-456"]`);

      expect(image).not.toBeNull();
    });

    it('renders document as DocumentAttachment when filename has .pdf extension', () => {
      const props: IRichTextProps = {
        text: `[report.pdf](${FILE_SERVICE_URL}/ghi-789)`,
        isMarkdownMode: true,
      };

      const { container } = render(<RichText {...props} />);
      const image = container.querySelector('img');

      expect(image).toBeNull();
      expect(container.textContent).toContain('report.pdf');
    });

    it('renders document as DocumentAttachment when filename has .docx extension', () => {
      const props: IRichTextProps = {
        text: `[document.docx](${FILE_SERVICE_URL}/jkl-012)`,
        isMarkdownMode: true,
      };

      const { container } = render(<RichText {...props} />);
      const image = container.querySelector('img');

      expect(image).toBeNull();
      expect(container.textContent).toContain('document.docx');
    });

    it('renders plain link when filename has no extension', () => {
      const props: IRichTextProps = {
        text: `[no-extension-file](${FILE_SERVICE_URL}/mno-345)`,
        isMarkdownMode: true,
      };

      const { container } = render(<RichText {...props} />);
      const link = container.querySelector(`a[href="${FILE_SERVICE_URL}/mno-345"]`);

      expect(link).not.toBeNull();
      expect(link?.textContent).toBe('no-extension-file');
    });

    it('renders mixed content with images and documents correctly', () => {
      const props: IRichTextProps = {
        text: [
          `[photo.png](${FILE_SERVICE_URL}/aaa)`,
          `[report.pdf](${FILE_SERVICE_URL}/bbb)`,
        ].join('\n'),
        isMarkdownMode: true,
      };

      const { container } = render(<RichText {...props} />);
      const images = container.querySelectorAll('img');

      expect(images).toHaveLength(1);
      expect(images[0].getAttribute('src')).toBe(`${FILE_SERVICE_URL}/aaa`);
      expect(container.textContent).toContain('report.pdf');
    });
  });
});
