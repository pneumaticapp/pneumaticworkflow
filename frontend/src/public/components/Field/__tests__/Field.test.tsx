import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Field } from '../Field';
import { EFieldTagName } from '../types';

jest.mock('../../RichEditor', () => ({
  RichEditor: ({ placeholder }: { placeholder?: string }) => (
    <div data-testid="rich-editor">{placeholder}</div>
  ),
}));

describe('Field component', () => {
  describe('Default input rendering', () => {
    it('renders input value, placeholder, and field type icon', () => {
      const mockIcon = <span data-testid="custom-icon">Icon</span>;

      render(
        <Field
          value="Test text"
          placeholder="Enter value"
          icon={mockIcon}
          onChange={jest.fn()}
        />,
      );

      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue('Test text');

      const iconElement = screen.getByTestId('custom-icon');
      expect(iconElement).toBeInTheDocument();
    });

    it('triggers onChange when typing text into input', () => {
      const handleChange = jest.fn();

      render(
        <Field
          value=""
          onChange={handleChange}
        />,
      );

      const input = screen.getByRole('textbox');
      userEvent.type(input, 'a');

      expect(handleChange).toHaveBeenCalledTimes(1);
    });

    it('disables input when disabled prop is true', () => {
      render(
        <Field
          value="Disabled value"
          disabled
          onChange={jest.fn()}
        />,
      );

      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
    });
  });

  describe('Textarea rendering mode', () => {
    it('renders textarea with field type icon when tagName=Textarea', () => {
      const mockIcon = <span data-testid="textarea-icon">Field icon</span>;

      render(
        <Field
          tagName={EFieldTagName.Textarea}
          value="Multiline text"
          icon={mockIcon}
          onChange={jest.fn()}
        />,
      );

      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('Multiline text');

      const iconElement = screen.getByTestId('textarea-icon');
      expect(iconElement).toBeInTheDocument();
    });
  });
});
