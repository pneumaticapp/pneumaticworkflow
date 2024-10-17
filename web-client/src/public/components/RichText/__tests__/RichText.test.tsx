/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { mount, render } from 'enzyme';
import { RichText, IRichTextProps } from '../RichText';

describe('RichText', () => {
  it('renderes correct html for mentions and links', () => {
    const props: IRichTextProps = {
      text: 'Hello, [Jyoti Puri|3], look here: link: http://pneumatic.app/',
      isMarkdownMode: true,
    };

    const wrapper = mount(<RichText {...props} />);

    expect(wrapper).toMatchSnapshot();
  });

  it('renderes mentions in different languages correctly', () => {
    const users = [
      {
        name: 'Алексей Карпов-Константинов',
        id: 3,
      },
      {
        name: 'Alex Karpov-Konstantinov',
        id: 4,
      },
      {
        name: 'אלכסיי קרפוב-קונסטנטינוב',
        id: 5,
      },
      {
        name: 'アレクセイカルポフ-コンスタンティノフ',
        id: 6,
      },
    ];
    const usersString = users.map(({ name, id }) => `[${name}|${id}]`).join(', ');
    const props: IRichTextProps = { text: `Hello, ${usersString}`, isMarkdownMode: true, };

    const wrapper = mount(<RichText {...props} />);

    for (let user of users) {
      expect(wrapper.text()).toContain(`@${user.name}`);
    }
  });

  it('renderes correct html for plain text', () => {
    const props: IRichTextProps = { text: 'Some plain text', isMarkdownMode: true, };

    const wrapper = mount(<RichText {...props} />);

    expect(wrapper).toMatchSnapshot();
  });

  it('clears xss', () => {
    const props: IRichTextProps = {
      text: '<script>console.log("I\'ll try to hack you")</script>',
      isMarkdownMode: false,
    };

    const wrapper = mount(<RichText {...props} />);

    expect(wrapper.text()).toBe('<script>console.log("I\'ll try to hack you")</script>');
  });

  it('empty render if text prop is null', () => {
    const props: IRichTextProps = { text: null, isMarkdownMode: true, };

    const wrapper = mount(<RichText {...props} />);

    expect(wrapper.isEmptyRender()).toBe(true);
  });

  it('RichText and youtube in text flag return text with youtube iframe', () => {
    const props: IRichTextProps = {
      text: 'test1 https://www.youtube.com/watch?v=jNQXAC9IVRw',
      isMarkdownMode: true,
    };

    const wrapper = render(<RichText {...props}/>);

    expect(wrapper).toMatchSnapshot();
  });

  it('RichText and loom link in text flag return text with loom iframe', () => {
    const props: IRichTextProps = {
      text: 'test1 https://www.loom.com/share/7f68fa7f01e349cab91b0c36168f68c3?t=1',
      isMarkdownMode: true,
    };

    const wrapper = render(<RichText {...props}/>);

    expect(wrapper).toMatchSnapshot();
  });

  it('RichText and youtube and loom link in text flag return text with youtube and loom iframe',
    () => {
      const props: IRichTextProps = {
        text: 'test1 https://www.loom.com/share/7f68fa7f01e349cab91b0c36168f68c3?t=1 https://www.youtube.com/watch?v=jNQXAC9IVRw',
        isMarkdownMode: true,
      };

      const wrapper = render(<RichText {...props}/>);

      expect(wrapper).toMatchSnapshot();
    });
});
