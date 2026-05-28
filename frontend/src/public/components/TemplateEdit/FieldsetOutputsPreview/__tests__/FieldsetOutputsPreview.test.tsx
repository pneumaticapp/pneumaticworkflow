import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { EExtraFieldType, IFieldsetData, ITaskFieldset } from '../../../../types/template';
import { FieldsetOutputsPreview } from '../FieldsetOutputsPreview';

const makeTaskFieldset = (apiName: string, order = 0): ITaskFieldset => ({ apiName, order });

const makeFieldsetData = (apiName: string, fieldsCount: number): IFieldsetData => ({
  id: 1,
  apiName,
  name: `Fieldset ${apiName}`,
  description: '',
  order: 0,
  fields: Array.from({ length: fieldsCount }, (_, i) => ({
    apiName: `field-${apiName}-${i}`,
    name: `Field ${i}`,
    type: EExtraFieldType.String,
    order: i,
    isRequired: false,
    isHidden: false,
    userId: null,
    groupId: null,
    description: '',
    selections: [],
  })),
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
        fieldsets: [makeTaskFieldset('not-in-map'), makeTaskFieldset('empty-fields')],
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
        fieldsets: [makeTaskFieldset('fs-a'), makeTaskFieldset('fs-b')],
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
        fieldsets: [makeTaskFieldset('fs-a')],
        fieldsetsByApiName,
        onGroupClick,
      }),
    );

    userEvent.click(screen.getByRole('button'));

    expect(onGroupClick).toHaveBeenCalledTimes(1);
  });
});
