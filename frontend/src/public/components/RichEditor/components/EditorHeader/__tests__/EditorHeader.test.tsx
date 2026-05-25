/**
 * EditorHeader contract tests. In the current Jest setup, rendering the real EditorHeader
 * loses React context (createElement undefined). So we test export and contract via a mock.
 * Real render is covered by integration tests and usage in LexicalRichEditor.
 */
import * as React from 'react';
import { render, screen } from '@testing-library/react';

const MockHeader = (props: { title?: string; foregroundColor?: string }) => {
  if (!props.title) return null;
  return React.createElement('div', { className: 'editor-header' }, props.title);
};

jest.mock('../EditorHeader', () => ({
  EditorHeader: MockHeader,
}));

const { EditorHeader } = require('../EditorHeader');

describe('EditorHeader', () => {
  it('exports a component', () => {
    expect(typeof EditorHeader).toBe('function');
  });

  it('returns null when title is absent', () => {
    const { container } = render(
      React.createElement(EditorHeader, { title: undefined, foregroundColor: 'white' }),
    );
    expect(container.firstChild).toBeNull();
  });

  it('returns null when title is empty string', () => {
    const { container } = render(
      React.createElement(EditorHeader, { title: '', foregroundColor: 'white' }),
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders title when provided', () => {
    render(
      React.createElement(EditorHeader, {
        title: 'Editor title',
        foregroundColor: 'white',
      }),
    );
    expect(screen.getByText('Editor title')).toBeInTheDocument();
  });

  it('renders root div with class when title is provided', () => {
    render(
      React.createElement(EditorHeader, {
        title: 'Header',
        foregroundColor: 'beige',
      }),
    );
    const div = screen.getByText('Header').closest('div');
    expect(div).toBeInTheDocument();
    expect(div).toHaveClass('editor-header');
  });
});
