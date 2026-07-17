import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldLabel, IFieldLabelProps } from '../FieldLabel';
import { EExtraFieldMode } from '../../../../../types/template';

jest.mock('react-textarea-autosize', () => {
  const ReactInsideMock = require('react');

  return {
    __esModule: true,
    default: ReactInsideMock.forwardRef(
      (
        props: {
          value: string;
          onChange: React.ChangeEventHandler<HTMLTextAreaElement>;
          placeholder: string;
          disabled: boolean;
          onFocus: () => void;
          onBlur: () => void;
        },
        ref: React.Ref<HTMLTextAreaElement>,
      ) =>
        ReactInsideMock.createElement('textarea', {
          value: props.value || '',
          onChange: props.onChange,
          placeholder: props.placeholder,
          disabled: props.disabled,
          onFocus: props.onFocus,
          onBlur: props.onBlur,
          ref,
          'aria-label': 'field name',
        }),
    ),
  };
});

jest.mock('../../../../icons', () => ({
  PencilSmallIcon: () => null,
}));

jest.mock('../getInputNameBackground', () => ({
  getInputNameBackground: jest.fn(() => ''),
}));

jest.mock('../../../../../utils/validators', () => ({
  validateKickoffFieldName: jest.fn(() => ''),
}));

describe('FieldLabel', () => {
  const mockHandleChangeName = jest.fn();

  const baseProps: Omit<IFieldLabelProps, 'mode'> = {
    name: 'My field',
    isRequired: false,
    isDisabled: false,
    handleChangeName: mockHandleChangeName,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Kickoff mode', () => {
    const kickoffProps: IFieldLabelProps = { ...baseProps, mode: EExtraFieldMode.Kickoff };

    it('renders editable textarea with field name', () => {
      render(<FieldLabel {...kickoffProps} />);

      const textarea = screen.getByRole('textbox', { name: 'field name' });
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('My field');
    });

    it('renders required sign when isRequired=true', () => {
      render(<FieldLabel {...kickoffProps} isRequired={true} />);

      expect(screen.getByLabelText('required')).toBeInTheDocument();
    });

    it('hides required sign when isRequired=false', () => {
      render(<FieldLabel {...kickoffProps} isRequired={false} />);

      expect(screen.queryByLabelText('required')).not.toBeInTheDocument();
    });

    it('renders edit button when textarea is not focused', () => {
      render(<FieldLabel {...kickoffProps} />);

      expect(screen.getByRole('button', { name: 'Edit field name' })).toBeInTheDocument();
    });

    it('hides edit button when textarea is focused', () => {
      render(<FieldLabel {...kickoffProps} />);

      const textarea = screen.getByRole('textbox', { name: 'field name' });
      userEvent.click(textarea);

      expect(screen.queryByRole('button', { name: 'Edit field name' })).not.toBeInTheDocument();
    });

    it('calls handleChangeName on textarea input', () => {
      render(<FieldLabel {...kickoffProps} />);

      const textarea = screen.getByRole('textbox', { name: 'field name' });
      userEvent.type(textarea, 'X');

      expect(mockHandleChangeName).toHaveBeenCalledTimes(1);
    });
  });

  describe('Non-kickoff mode', () => {
    const processRunProps: IFieldLabelProps = { ...baseProps, mode: EExtraFieldMode.ProcessRun };
    it('renders readonly name text', () => {
      render(<FieldLabel {...processRunProps} />);

      expect(screen.getByText('My field')).toBeInTheDocument();
      expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    });

    it('renders required sign when isRequired=true', () => {
      render(<FieldLabel {...processRunProps} isRequired={true} />);

      expect(screen.getByLabelText('required')).toBeInTheDocument();
    });

    it('hides required sign when isRequired=false', () => {
      render(<FieldLabel {...processRunProps} isRequired={false} />);

      expect(screen.queryByLabelText('required')).not.toBeInTheDocument();
    });
  });
});
