import { createElement } from 'react';
import { render, act } from '@testing-library/react';
import { useLinkActions } from '../useLinkActions';

const TOGGLE_LINK_COMMAND = 'TOGGLE_LINK_COMMAND';
jest.mock('@lexical/link', () => ({ TOGGLE_LINK_COMMAND: 'TOGGLE_LINK_COMMAND' }));

const mockDispatchCommand = jest.fn();

const mockEditor = {
  dispatchCommand: mockDispatchCommand,
  update: (fn: () => void) => {
    fn();
  },
} as unknown as import('lexical').LexicalEditor;

describe('useLinkActions', () => {
  const onFormClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('dispatches TOGGLE_LINK_COMMAND and calls onFormClose when applyLink(url) is called without linkText', () => {
    let applyLink: (url: string, linkText?: string) => void;
    const Inner = () => {
      const actions = useLinkActions(mockEditor, onFormClose);
      applyLink = actions.applyLink;
      return null;
    };
    render(createElement(Inner, null));
    act(() => {
      applyLink!('https://example.com');
    });
    expect(mockDispatchCommand).toHaveBeenCalledWith(TOGGLE_LINK_COMMAND, 'https://example.com');
    expect(onFormClose).toHaveBeenCalled();
  });
});
