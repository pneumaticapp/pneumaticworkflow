import * as React from 'react';
import { render } from '@testing-library/react';
import { RichText, IRichTextProps } from '../RichText';

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

  it('clears xss', () => {
    const props: IRichTextProps = {
      text: '<script>console.log("I\'ll try to hack you")</script>',
      isMarkdownMode: false,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.textContent).toContain('<script>console.log("I\'ll try to hack you")</script>');
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

    expect(container.firstChild).toMatchSnapshot();
  });

  it('RichText and loom link in text flag return text with loom iframe', () => {
    const props: IRichTextProps = {
      text: 'test1 https://www.loom.com/share/7f68fa7f01e349cab91b0c36168f68c3?t=1',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

    expect(container.firstChild).toMatchSnapshot();
  });

  it('RichText and youtube and loom link in text flag return text with youtube and loom iframe', () => {
    const props: IRichTextProps = {
      text: 'test1 https://www.loom.com/share/7f68fa7f01e349cab91b0c36168f68c3?t=1 https://www.youtube.com/watch?v=jNQXAC9IVRw',
      isMarkdownMode: true,
    };

    const { container } = render(<RichText {...props} />);

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
});
