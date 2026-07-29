import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { makeFieldsetBindingClient, makeFieldsetField } from '../../../../__stubs__/fieldsets.factory';
import { FieldsetOutputsPreview } from '../FieldsetOutputsPreview';

describe('FieldsetOutputsPreview', () => {
  const getFieldsetButton = (fieldsetName: string) =>
    screen.getByRole('button', { name: new RegExp(fieldsetName) });

  it('returns null when fieldsets array is empty', () => {
    const { container } = render(
      React.createElement(FieldsetOutputsPreview, {
        fieldsets: [],
      }),
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('returns null when no fieldset has fields', () => {
    const { container } = render(
      React.createElement(FieldsetOutputsPreview, {
        fieldsets: [
          makeFieldsetBindingClient({ apiNameBinding: 'fs-1', fields: [] }),
          makeFieldsetBindingClient({ apiNameBinding: 'fs-2', fields: [] }),
        ],
      }),
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders one button per fieldset that has fields', () => {
    render(
      React.createElement(FieldsetOutputsPreview, {
        fieldsets: [
          makeFieldsetBindingClient({
            apiNameBinding: 'fs-a',
            name: 'Fieldset A',
            fields: [makeFieldsetField({ apiName: 'f-1' }), makeFieldsetField({ apiName: 'f-2' })],
          }),
          makeFieldsetBindingClient({
            apiNameBinding: 'fs-b',
            name: 'Fieldset B',
            fields: [makeFieldsetField({ apiName: 'f-3' })],
          }),
        ],
        onGroupClick: jest.fn(),
      }),
    );

    expect(screen.getAllByRole('button')).toHaveLength(2);
    expect(getFieldsetButton('Fieldset A')).toBeInTheDocument();
    expect(getFieldsetButton('Fieldset B')).toBeInTheDocument();
  });

  it('click on button calls onGroupClick exactly once', () => {
    const onGroupClick = jest.fn();

    render(
      React.createElement(FieldsetOutputsPreview, {
        fieldsets: [
          makeFieldsetBindingClient({
            apiNameBinding: 'fs-a',
            name: 'Fieldset A',
            fields: [makeFieldsetField({ apiName: 'f-1' })],
          }),
        ],
        onGroupClick,
      }),
    );

    userEvent.click(screen.getByRole('button'));

    expect(onGroupClick).toHaveBeenCalledTimes(1);
  });
});
