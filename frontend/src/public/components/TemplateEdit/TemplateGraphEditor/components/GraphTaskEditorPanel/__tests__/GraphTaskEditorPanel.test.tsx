import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IntlProvider } from 'react-intl';
import { configure } from '@testing-library/react';

import { GraphTaskEditorPanel } from '../GraphTaskEditorPanel';
import { enMessages } from '../../../../../../lang/locales/en_US';

configure({ testIdAttribute: 'data-test-id' });

const renderPanel = (onClose = jest.fn()) =>
  render(
    <div>
      <button type="button">outside</button>
      <IntlProvider locale="en" messages={enMessages}>
        <GraphTaskEditorPanel onClose={onClose}>
          <div>task-form-content</div>
        </GraphTaskEditorPanel>
      </IntlProvider>
    </div>,
  );

describe('GraphTaskEditorPanel', () => {
  it('should render the task form over the graph canvas', () => {
    renderPanel();

    expect(screen.getByTestId('graph-task-editor')).toBeInTheDocument();
    expect(screen.getByText('task-form-content')).toBeInTheDocument();
  });

  it('should close the panel when the close icon is clicked', () => {
    const onClose = jest.fn();
    renderPanel(onClose);

    userEvent.click(screen.getByTestId('graph-task-editor-close'));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should close the panel when the user clicks outside the form', () => {
    const onClose = jest.fn();
    renderPanel(onClose);

    userEvent.click(screen.getByRole('button', { name: 'outside' }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('should keep the panel open when the user clicks inside the form', () => {
    const onClose = jest.fn();
    renderPanel(onClose);

    userEvent.click(screen.getByText('task-form-content'));

    expect(onClose).not.toHaveBeenCalled();
  });

  it('should mount the panel on document body', () => {
    renderPanel();

    expect(document.body.querySelector('[data-test-id="graph-task-editor"]')).toBeInTheDocument();
  });
});
