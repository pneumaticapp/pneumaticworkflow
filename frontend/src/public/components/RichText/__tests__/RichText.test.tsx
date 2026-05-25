import * as React from 'react';
import { render } from '@testing-library/react';
import { RichText, IRichTextProps } from '../RichText';
import { intlMock } from '../../../__stubs__/intlMock';
import { EExtraFieldType } from '../../../types/template';
import { TTaskVariable } from '../../TemplateEdit/types';
import {
  WORKFLOW_STARTER_VARIABLE_API_NAME,
  WORKFLOW_STARTER_VARIABLE_TITLE,
} from '../../TemplateEdit/TaskForm/utils/getTaskVariables';

describe('RichText', () => {
  const LOCALIZED_WF_STARTER_TITLE = intlMock.formatMessage({ id: 'kickoff.system-varibale-workflow-starter' });

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
});
