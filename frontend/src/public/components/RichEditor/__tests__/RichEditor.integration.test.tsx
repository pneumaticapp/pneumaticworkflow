/**
 * Editor interaction specs: insertion, deletion, Undo/Redo, cursor.
 * These scenarios are implemented below but SKIPPED in Jest because the real Lexical editor
 * does not complete mount in JSDOM (scheduler/RAF). Run the same scenarios in E2E (e.g. Playwright).
 *
 * Stack: Jest + React Testing Library + user-event (v13). When run in a real browser,
 * use getByTestId('rich-editor-contenteditable'), userEvent.type/keyboard, and assert
 * both DOM text and handleChange(markdown).
 */

import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const getEditable = () =>
  screen.getByTestId('rich-editor-contenteditable');

const getEditableText = (el: HTMLElement): string =>
  (el.textContent ?? '').replace(/\u00A0/g, ' ').trim();

describe('RichEditor integration (E2E specs)', () => {
  const defaultProps = {
    handleChange: jest.fn(),
    withToolbar: false,
    withMentions: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('smoke: integration spec file and helpers are loaded (real editor requires E2E)', () => {
    expect(getEditableText).toBeDefined();
    expect(defaultProps.handleChange).toBeDefined();
  });

  describe('text insertion (run in E2E)', () => {
    it.skip('inserts text into empty document and updates both DOM and handleChange', async () => {
      const { RichEditor } = await import('../lexical');
      const handleChange = jest.fn();

      render(<RichEditor {...defaultProps} handleChange={handleChange} />);
      const editable = getEditable();
      editable.focus();

      await userEvent.type(editable, 'Hello');

      expect(getEditableText(editable)).toBe('Hello');
      expect(handleChange).toHaveBeenCalled();
      const lastMarkdown = handleChange.mock.calls[handleChange.mock.calls.length - 1][0];
      expect(lastMarkdown).toContain('Hello');
    });

    it.skip('inserts text in the middle of existing text and keeps cursor correct', async () => {
      const { RichEditor } = await import('../lexical');
      const handleChange = jest.fn();

      render(
        <RichEditor
          {...defaultProps}
          handleChange={handleChange}
          defaultValue="ab"
        />,
      );
      const editable = getEditable();
      editable.focus();

      userEvent.keyboard('{ArrowLeft}');
      await userEvent.type(editable, 'X');

      const text = getEditableText(editable);
      expect(text).toBe('aXb');
      const lastMarkdown = handleChange.mock.calls[handleChange.mock.calls.length - 1][0];
      expect(lastMarkdown).toContain('aXb');
      expect(document.activeElement).toBe(editable);
    });
  });

  describe('deletion (run in E2E)', () => {
    it.skip('Backspace removes character before cursor and updates DOM and data', async () => {
      const { RichEditor } = await import('../lexical');
      const handleChange = jest.fn();

      render(<RichEditor {...defaultProps} handleChange={handleChange} />);
      const editable = getEditable();
      editable.focus();

      await userEvent.type(editable, 'ab');
      expect(getEditableText(editable)).toBe('ab');

      userEvent.keyboard('{Backspace}');

      expect(getEditableText(editable)).toBe('a');
      const lastMarkdown = handleChange.mock.calls[handleChange.mock.calls.length - 1][0];
      expect(lastMarkdown).toContain('a');
      expect(lastMarkdown).not.toContain('ab');
    });

    it.skip('Delete removes character after cursor (selected forward) and updates DOM and data', async () => {
      const { RichEditor } = await import('../lexical');
      const handleChange = jest.fn();

      render(<RichEditor {...defaultProps} handleChange={handleChange} />);
      const editable = getEditable();
      editable.focus();

      await userEvent.type(editable, 'ab');
      userEvent.keyboard('{ArrowLeft}');
      userEvent.keyboard('{Delete}');

      expect(getEditableText(editable)).toBe('a');
      const lastMarkdown = handleChange.mock.calls[handleChange.mock.calls.length - 1][0];
      expect(lastMarkdown).toContain('a');
      expect(document.activeElement).toBe(editable);
    });
  });

  describe('Undo / Redo (run in E2E)', () => {
    it.skip('Undo reverts at least 3 steps; Redo restores them; cursor stays in editor', async () => {
      const { RichEditor } = await import('../lexical');
      const handleChange = jest.fn();

      render(<RichEditor {...defaultProps} handleChange={handleChange} />);
      const editable = getEditable();
      editable.focus();

      await userEvent.type(editable, '1');
      await userEvent.type(editable, '2');
      await userEvent.type(editable, '3');

      expect(getEditableText(editable)).toBe('123');

      userEvent.keyboard('{Control>}z{/Control}');
      userEvent.keyboard('{Control>}z{/Control}');
      userEvent.keyboard('{Control>}z{/Control}');

      const afterUndo = getEditableText(editable);
      expect(afterUndo).toBe('');
      expect(document.activeElement).toBe(editable);

      userEvent.keyboard('{Control>}{Shift>}z{/Shift}{/Control}');
      userEvent.keyboard('{Control>}{Shift>}z{/Shift}{/Control}');
      userEvent.keyboard('{Control>}{Shift>}z{/Shift}{/Control}');

      expect(getEditableText(editable)).toBe('123');
      const lastMarkdown = handleChange.mock.calls[handleChange.mock.calls.length - 1][0];
      expect(lastMarkdown).toContain('123');
      expect(document.activeElement).toBe(editable);
    });
  });

  describe('cursor (caret) after operations (run in E2E)', () => {
    it.skip('editable keeps focus and correct visible content after insert', async () => {
      const { RichEditor } = await import('../lexical');
      render(<RichEditor {...defaultProps} handleChange={jest.fn()} />);
      const editable = getEditable();
      editable.focus();
      await userEvent.type(editable, 'x');

      expect(document.activeElement).toBe(editable);
      expect(getEditableText(editable)).toBe('x');
    });

    it.skip('editable keeps focus after Backspace', async () => {
      const { RichEditor } = await import('../lexical');
      render(<RichEditor {...defaultProps} handleChange={jest.fn()} />);
      const editable = getEditable();
      editable.focus();
      await userEvent.type(editable, 'ab');
      userEvent.keyboard('{Backspace}');

      expect(document.activeElement).toBe(editable);
      expect(getEditableText(editable)).toBe('a');
    });

    it.skip('editable keeps focus after Delete', async () => {
      const { RichEditor } = await import('../lexical');
      render(<RichEditor {...defaultProps} handleChange={jest.fn()} />);
      const editable = getEditable();
      editable.focus();
      await userEvent.type(editable, 'ab');
      userEvent.keyboard('{ArrowLeft}');
      userEvent.keyboard('{Delete}');

      expect(document.activeElement).toBe(editable);
      expect(getEditableText(editable)).toBe('a');
    });

    it.skip('editable keeps focus after Undo and Redo', async () => {
      const { RichEditor } = await import('../lexical');
      render(<RichEditor {...defaultProps} handleChange={jest.fn()} />);
      const editable = getEditable();
      editable.focus();
      await userEvent.type(editable, 'a');
      userEvent.keyboard('{Control>}z{/Control}');
      userEvent.keyboard('{Control>}{Shift>}z{/Shift}{/Control}');

      expect(document.activeElement).toBe(editable);
      expect(getEditableText(editable)).toBe('a');
    });
  });
});
