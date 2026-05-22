import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { FieldsetFieldGroup } from '../FieldsetFieldGroup';
import { EExtraFieldType, EExtraFieldMode, IExtraField } from '../../../types/template';
import { EInputNameBackgroundColor } from '../../../types/workflow';

type TExtraFieldIntlMockProps = {
  field: IExtraField;
  editField: (changedProps: Partial<IExtraField>) => void;
};

jest.mock('../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn(({ field, editField }: TExtraFieldIntlMockProps) => (
    <div data-testid={`extra-field-${field.apiName}`}>
      <span>{field.name}</span>
      <button
        type="button"
        onClick={() => editField({ value: `value-for-${field.apiName}` })}
      >
        edit {field.apiName}
      </button>
    </div>
  )),
}));

const makeField = (apiName: string, order = 0): IExtraField => ({
  apiName,
  name: `Field ${apiName}`,
  type: EExtraFieldType.String,
  order,
  isRequired: false,
  isHidden: false,
  userId: null,
  groupId: null,
});

const baseProps = {
  fields: [] as IExtraField[],
  onEditField: jest.fn(() => jest.fn()),
  mode: EExtraFieldMode.Kickoff,
  labelBackgroundColor: EInputNameBackgroundColor.White,
  accountId: 1,
};

describe('FieldsetFieldGroup', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('group title', () => {
    it('renders when title is a non-empty string', () => {
      render(<FieldsetFieldGroup {...baseProps} title="Contact details" />);

      expect(screen.getByText('Contact details')).toBeInTheDocument();
    });

    it('does not render when title is omitted', () => {
      render(<FieldsetFieldGroup {...baseProps} />);

      expect(screen.queryByText('Contact details')).not.toBeInTheDocument();
    });
  });

  describe('group description', () => {
    it('renders when description is a non-empty string', () => {
      render(<FieldsetFieldGroup {...baseProps} description="Fill carefully" />);

      expect(screen.getByText('Fill carefully')).toBeInTheDocument();
    });

    it('renders even when title is omitted (independent of title)', () => {
      render(<FieldsetFieldGroup {...baseProps} description="Description only" />);

      expect(screen.queryByText('Contact details')).not.toBeInTheDocument();
      expect(screen.getByText('Description only')).toBeInTheDocument();
    });
  });

  describe('validation error message', () => {
    const ERROR_TEXT = 'Required field';

    it('is visible when validationError is a non-empty string', () => {
      render(<FieldsetFieldGroup {...baseProps} validationError={ERROR_TEXT} />);

      expect(screen.getByText(ERROR_TEXT)).toBeInTheDocument();
    });

    it.each<'' | null | undefined>(['', null, undefined])(
      'does not render for falsy validationError = %p',
      (value) => {
        render(<FieldsetFieldGroup {...baseProps} validationError={value} />);

        expect(screen.queryByText(ERROR_TEXT)).not.toBeInTheDocument();
      },
    );
  });

  it('renders all provided fields in the original array order, without re-sorting', () => {
    const fields = [
      makeField('email', 5),
      makeField('phone', 1),
      makeField('city', 3),
    ];

    render(<FieldsetFieldGroup {...baseProps} fields={fields} />);

    const rendered = screen.getAllByTestId(/^extra-field-/);

    expect(rendered).toHaveLength(3);
    expect(rendered.map((el) => el.getAttribute('data-testid'))).toEqual([
      'extra-field-email',
      'extra-field-phone',
      'extra-field-city',
    ]);
  });

  it('routes edits to the specific apiName when editing a field', () => {
    const collected: Array<{ apiName: string; changedProps: Partial<IExtraField> }> = [];
    const onEditField = jest.fn(
      (apiName: string) => (changedProps: Partial<IExtraField>) => {
        collected.push({ apiName, changedProps });
      },
    );

    const fields = [makeField('email'), makeField('phone'), makeField('city')];

    render(
      <FieldsetFieldGroup {...baseProps} fields={fields} onEditField={onEditField} />,
    );

    expect(onEditField).toHaveBeenCalledTimes(3);
    expect(onEditField.mock.calls.map(([apiName]) => apiName)).toEqual([
      'email',
      'phone',
      'city',
    ]);

    userEvent.click(screen.getByRole('button', { name: 'edit phone' }));

    expect(collected).toEqual([
      { apiName: 'phone', changedProps: { value: 'value-for-phone' } },
    ]);
  });
});
