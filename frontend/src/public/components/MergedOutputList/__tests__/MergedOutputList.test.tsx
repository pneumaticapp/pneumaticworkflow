import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { MergedOutputList } from '../MergedOutputList';
import { EExtraFieldType, IExtraField, IFieldsetData } from '../../../types/template';
import { EFieldLabelPosition } from '../../../types/fieldset';
import { EInputNameBackgroundColor } from '../../../types/workflow';

jest.mock('../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn(({ field }: { field: IExtraField }) => (
    <div data-testid="extra-field">{field.apiName}</div>
  )),
}));

jest.mock('../../FieldsetFieldGroup', () => ({
  FieldsetFieldGroup: jest.fn(({ title }: { title: string }) => (
    <div data-testid="fieldset-group">{title}</div>
  )),
}));

const makeField = (apiName: string, order: number): IExtraField => ({
  apiName,
  name: apiName,
  type: EExtraFieldType.String,
  order,
  isRequired: false,
  isHidden: false,
  userId: null,
  groupId: null,
});

const makeFieldset = (id: number, name: string, order: number): IFieldsetData => ({
  id,
  apiName: `fs-${id}`,
  name,
  description: '',
  fields: [],
  order,
  labelPosition: EFieldLabelPosition.Top,
});

const baseProps = {
  onEditField: jest.fn(() => jest.fn()),
  onEditFieldsetField: jest.fn(() => jest.fn()),
  labelBackgroundColor: EInputNameBackgroundColor.White,
  accountId: 1,
};

describe('MergedOutputList', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders fields and fieldsets interleaved by order', () => {
    const fields = [makeField('field-a', 1), makeField('field-b', 3)];
    const fieldsets = [makeFieldset(10, 'Fieldset Middle', 2)];

    const { container } = render(
      <MergedOutputList {...baseProps} fields={fields} fieldsets={fieldsets} />,
    );

    const items = container.querySelectorAll('[data-testid="extra-field"], [data-testid="fieldset-group"]');
    expect(items).toHaveLength(3);

    expect(items[0].textContent).toBe('field-b');
    expect(items[1].textContent).toBe('Fieldset Middle');
    expect(items[2].textContent).toBe('field-a');
  });

  it('renders only fields when no fieldsets provided', () => {
    const fields = [makeField('solo', 0)];

    render(<MergedOutputList {...baseProps} fields={fields} />);

    expect(screen.getAllByTestId('extra-field')).toHaveLength(1);
    expect(screen.queryByTestId('fieldset-group')).toBeNull();
  });

  it('renders only fieldsets when fields array is empty', () => {
    const fieldsets = [makeFieldset(1, 'Only FS', 0)];

    render(<MergedOutputList {...baseProps} fields={[]} fieldsets={fieldsets} />);

    expect(screen.queryByTestId('extra-field')).toBeNull();
    expect(screen.getAllByTestId('fieldset-group')).toHaveLength(1);
  });

  it('renders nothing when both arrays are empty', () => {
    const { container } = render(<MergedOutputList {...baseProps} fields={[]} fieldsets={[]} />);

    expect(container.childElementCount).toBe(0);
  });
});
