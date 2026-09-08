import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldsetSettings } from '../FieldsetSettings';
import { intlMock } from '../../../../../__stubs__/intlMock';
import { EFieldLabelPosition } from '../../../../../types/fieldset';
import { FilterSelect } from '../../../../UI';

jest.mock('react-textarea-autosize', () => {
  const actual = jest.requireActual('react');
  return {
    __esModule: true,
    default: actual.forwardRef(
      ({ minRows: _minRows, ...rest }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { minRows?: number }, ref: React.Ref<HTMLTextAreaElement>) =>
        actual.createElement('textarea', { ...rest, ref }),
    ),
  };
});

jest.mock('../../../../UI', () => ({
  Tooltip: jest.fn(({ children }: { children: React.ReactNode }) => children),
  FilterSelect: jest.fn(() => null),
}));

jest.mock('../../../../icons', () => ({
  FilledInfoIcon: () => null,
}));

function requireJestMock(value: unknown, label: string): jest.Mock {
  if (!jest.isMockFunction(value)) {
    throw new Error(`${label} is not a jest.Mock`);
  }
  return value;
}

const formatMsg = (id: string) => intlMock.formatMessage({ id });

type TFilterSelectProps = {
  options: { id: EFieldLabelPosition; name: string }[];
  selectedOption: EFieldLabelPosition;
  isDisabled: boolean;
  onChange: (key: string | null) => void;
};

const getFilterSelectProps = (): TFilterSelectProps => {
  const mock = requireJestMock(FilterSelect, 'FilterSelect');
  if (mock.mock.calls.length === 0) {
    throw new Error('FilterSelect was not rendered');
  }
  return mock.mock.calls[0][0] as TFilterSelectProps;
};

const makeProps = (overrides: Partial<React.ComponentProps<typeof FieldsetSettings>> = {}) => ({
  title: 'Test Title',
  description: 'Test Description',
  labelPosition: EFieldLabelPosition.Top,
  isReadOnly: false,
  isTitleError: false,
  onTitleChange: jest.fn(),
  onDescriptionChange: jest.fn(),
  onLabelPositionChange: jest.fn(),
  ...overrides,
});

describe('FieldsetSettings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('when isReadOnly=false', () => {
    it('renders editable title input with provided value', () => {
      render(React.createElement(FieldsetSettings, makeProps()));

      const input = screen.getByLabelText(formatMsg('fieldsets.settings.title'), { selector: 'input' });
      expect(input).toBeInTheDocument();
      expect(input).toHaveValue('Test Title');
      expect(input).not.toBeDisabled();
    });

    it('renders editable description textarea with provided value', () => {
      render(React.createElement(FieldsetSettings, makeProps()));

      const textarea = screen.getByLabelText(formatMsg('fieldsets.settings.description'));
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveValue('Test Description');
      expect(textarea).not.toBeDisabled();
    });

    it('calls onTitleChange on title input', () => {
      const onTitleChange = jest.fn();
      render(React.createElement(FieldsetSettings, makeProps({ onTitleChange })));

      const input = screen.getByLabelText(formatMsg('fieldsets.settings.title'), { selector: 'input' });
      userEvent.type(input, 'A');

      expect(onTitleChange).toHaveBeenCalledTimes(1);
    });

    it('calls onDescriptionChange on description input', () => {
      const onDescriptionChange = jest.fn();
      render(React.createElement(FieldsetSettings, makeProps({ onDescriptionChange })));

      const textarea = screen.getByLabelText(formatMsg('fieldsets.settings.description'));
      userEvent.type(textarea, 'B');

      expect(onDescriptionChange).toHaveBeenCalledTimes(1);
    });

    it('does not render readonly badge', () => {
      render(React.createElement(FieldsetSettings, makeProps()));

      expect(screen.queryByText(formatMsg('fieldsets.readonly-badge'))).not.toBeInTheDocument();
    });
  });

  describe('when isReadOnly=true', () => {
    it('renders disabled textarea for title', () => {
      render(React.createElement(FieldsetSettings, makeProps({ isReadOnly: true })));

      const titleTextarea = screen.getByDisplayValue('Test Title');
      expect(titleTextarea).toBeDisabled();
    });

    it('renders disabled textarea for description', () => {
      render(React.createElement(FieldsetSettings, makeProps({ isReadOnly: true })));

      const descTextarea = screen.getByDisplayValue('Test Description');
      expect(descTextarea).toBeDisabled();
    });

    it('renders readonly badge', () => {
      render(React.createElement(FieldsetSettings, makeProps({ isReadOnly: true })));

      expect(screen.getByText(formatMsg('fieldsets.readonly-badge'))).toBeInTheDocument();
    });

    it('passes isDisabled=true to FilterSelect', () => {
      render(React.createElement(FieldsetSettings, makeProps({ isReadOnly: true })));

      const props = getFilterSelectProps();
      expect(props.isDisabled).toBe(true);
    });
  });

  describe('FilterSelect label position', () => {
    it('passes options from FIELDSET_LABEL_POSITION_OPTIONS', () => {
      render(React.createElement(FieldsetSettings, makeProps()));

      const props = getFilterSelectProps();

      expect(props.options).toEqual(
        expect.arrayContaining([
          expect.objectContaining({ id: EFieldLabelPosition.Top }),
          expect.objectContaining({ id: EFieldLabelPosition.Left }),
        ]),
      );
      expect(props.options).toHaveLength(2);
    });

    it('passes selectedOption from labelPosition prop', () => {
      render(React.createElement(FieldsetSettings, makeProps({ labelPosition: EFieldLabelPosition.Left })));

      const props = getFilterSelectProps();
      expect(props.selectedOption).toBe(EFieldLabelPosition.Left);
    });

    it('calls onLabelPositionChange when position changes', () => {
      const onLabelPositionChange = jest.fn();
      render(React.createElement(FieldsetSettings, makeProps({ onLabelPositionChange })));

      const props = getFilterSelectProps();
      props.onChange(EFieldLabelPosition.Left);

      expect(onLabelPositionChange).toHaveBeenCalledTimes(1);
      expect(onLabelPositionChange).toHaveBeenCalledWith(EFieldLabelPosition.Left);
    });

    it('does not call onLabelPositionChange when same value is selected', () => {
      const onLabelPositionChange = jest.fn();
      render(React.createElement(FieldsetSettings, makeProps({
        labelPosition: EFieldLabelPosition.Top,
        onLabelPositionChange,
      })));

      const props = getFilterSelectProps();
      props.onChange(EFieldLabelPosition.Top);

      expect(onLabelPositionChange).not.toHaveBeenCalled();
    });
  });
});
