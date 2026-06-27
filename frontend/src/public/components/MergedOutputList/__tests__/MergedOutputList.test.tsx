import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { MergedOutputList } from '../MergedOutputList';
import { makeExtraField } from '../../../__stubs__/fields.factory';
import { makeFieldsetData } from '../../../__stubs__/fieldsets.factory';
import { IExtraField } from '../../../types/template';
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
    const fields = [
      makeExtraField({ apiName: 'field-a', name: 'field-a', order: 1 }),
      makeExtraField({ apiName: 'field-b', name: 'field-b', order: 3 }),
    ];
    const fieldsets = [makeFieldsetData({ sharedFieldsetId: 10, apiName: 'fs-10', name: 'Fieldset Middle', order: 2 })];

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
    const fields = [makeExtraField({ apiName: 'solo', name: 'solo' })];

    render(<MergedOutputList {...baseProps} fields={fields} />);

    expect(screen.getAllByTestId('extra-field')).toHaveLength(1);
    expect(screen.queryByTestId('fieldset-group')).toBeNull();
  });

  it('renders only fieldsets when fields array is empty', () => {
    const fieldsets = [makeFieldsetData({ name: 'Only FS' })];

    render(<MergedOutputList {...baseProps} fields={[]} fieldsets={fieldsets} />);

    expect(screen.queryByTestId('extra-field')).toBeNull();
    expect(screen.getAllByTestId('fieldset-group')).toHaveLength(1);
  });

  it('renders nothing when both arrays are empty', () => {
    const { container } = render(<MergedOutputList {...baseProps} fields={[]} fieldsets={[]} />);

    expect(container.childElementCount).toBe(0);
  });
});
