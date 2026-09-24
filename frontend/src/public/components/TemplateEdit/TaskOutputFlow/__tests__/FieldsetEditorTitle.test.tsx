import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldsetEditorTitle } from '../FieldsetEditorTitle';
import { intlMock } from '../../../../__stubs__/intlMock';

jest.mock('../../../icons', () => ({
  PencilSmallIcon: () => React.createElement('svg', { 'data-testid': 'pencil-icon' }),
}));

jest.mock('../../../../utils/validators', () => ({
  validateFieldsetTitle: jest.fn((val: string) => (val ? '' : 'Title is required')),
}));

describe('FieldsetEditorTitle', () => {
  const mockOnEditFieldsetTitle = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const DEFAULT_PROPS = {
    apiNameBinding: 'fs-binding-1',
    title: 'Initial Fieldset Title',
    onEditFieldsetTitle: mockOnEditFieldsetTitle,
    formatMessage: intlMock.formatMessage,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders title label, textarea with initial value, and pencil icon', () => {
      render(React.createElement(FieldsetEditorTitle, DEFAULT_PROPS));

      expect(screen.getByText(`${formatMsg('fieldsets.title-label')}:`)).toBeInTheDocument();

      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveValue('Initial Fieldset Title');

      expect(screen.getByTestId('pencil-icon')).toBeInTheDocument();
    });
  });

  describe('Editing and callbacks', () => {
    it('calls onEditFieldsetTitle on blur when value changes', () => {
      render(React.createElement(FieldsetEditorTitle, DEFAULT_PROPS));

      const textarea = screen.getByRole('textbox');

      userEvent.clear(textarea);
      userEvent.type(textarea, 'New Fieldset Title');
      textarea.blur();

      expect(mockOnEditFieldsetTitle).toHaveBeenCalledTimes(1);
      expect(mockOnEditFieldsetTitle).toHaveBeenCalledWith('fs-binding-1', 'New Fieldset Title');
    });

    it('does NOT call onEditFieldsetTitle if title value did not change on blur', () => {
      render(React.createElement(FieldsetEditorTitle, DEFAULT_PROPS));

      const textarea = screen.getByRole('textbox');

      userEvent.click(textarea);
      textarea.blur();

      expect(mockOnEditFieldsetTitle).not.toHaveBeenCalled();
    });

    it('blurs textarea when Enter key is pressed', () => {
      render(React.createElement(FieldsetEditorTitle, DEFAULT_PROPS));

      const textarea = screen.getByRole('textbox');
      userEvent.click(textarea);

      userEvent.type(textarea, '{enter}');

      expect(screen.getByTestId('pencil-icon')).toBeInTheDocument();
    });
  });
});
