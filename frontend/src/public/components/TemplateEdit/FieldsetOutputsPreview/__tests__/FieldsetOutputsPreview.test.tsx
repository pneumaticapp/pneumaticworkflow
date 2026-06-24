import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { IFieldsetData } from '../../../../types/template';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetData as makeFieldsetDataBase, makeFieldsetBindingClient } from '../../../../__stubs__/fieldsets.factory';
import { FieldsetOutputsPreview } from '../FieldsetOutputsPreview';

const makeFieldsetData = (apiName: string, fieldsCount: number): IFieldsetData =>
  makeFieldsetDataBase({
    apiName,
    name: `Fieldset ${apiName}`,
    fields: Array.from({ length: fieldsCount }, (_, i) =>
      makeExtraField({
        apiName: `field-${apiName}-${i}`,
        name: `Field ${i}`,
        order: i,
      }),
    ),
  });

describe('FieldsetOutputsPreview', () => {
  const getFieldsetButton = (fieldsetName: string) =>
    screen.getByRole('button', { name: new RegExp(fieldsetName) });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns null when fieldsets array is empty', () => {
    const { container } = render(
      React.createElement(FieldsetOutputsPreview, {
        fieldsets: [],
        fieldsetsByApiName: new Map(),
      }),
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('returns null when no fieldset produces visible fields', () => {
    const fieldsetsByApiName = new Map<string, IFieldsetData>([
      ['empty-fields', makeFieldsetData('empty-fields', 0)],
    ]);

    const { container } = render(
      React.createElement(FieldsetOutputsPreview, {
        fieldsets: [makeFieldsetBindingClient({ apiName: 'not-in-map' }), makeFieldsetBindingClient({ apiName: 'empty-fields' })],
        fieldsetsByApiName,
      }),
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders one button per fieldset that has fields', () => {
    const fieldsetsByApiName = new Map<string, IFieldsetData>([
      ['fs-a', makeFieldsetData('fs-a', 2)],
      ['fs-b', makeFieldsetData('fs-b', 1)],
    ]);

    render(
      React.createElement(FieldsetOutputsPreview, {
        fieldsets: [makeFieldsetBindingClient({ apiName: 'fs-a' }), makeFieldsetBindingClient({ apiName: 'fs-b' })],
        fieldsetsByApiName,
        onGroupClick: jest.fn(),
      }),
    );

    expect(screen.getAllByRole('button')).toHaveLength(2);
    expect(getFieldsetButton('Fieldset fs-a')).toBeInTheDocument();
    expect(getFieldsetButton('Fieldset fs-b')).toBeInTheDocument();
  });

  it('click on button calls onGroupClick exactly once', () => {
    const onGroupClick = jest.fn();
    const fieldsetsByApiName = new Map<string, IFieldsetData>([
      ['fs-a', makeFieldsetData('fs-a', 1)],
    ]);

    render(
      React.createElement(FieldsetOutputsPreview, {
        fieldsets: [makeFieldsetBindingClient({ apiName: 'fs-a' })],
        fieldsetsByApiName,
        onGroupClick,
      }),
    );

    userEvent.click(screen.getByRole('button'));

    expect(onGroupClick).toHaveBeenCalledTimes(1);
  });
});
