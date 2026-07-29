import * as React from 'react';
import { render, screen } from '@testing-library/react';

import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetBindingClient, makeFieldsetField } from '../../../../__stubs__/fieldsets.factory';
import { IExtraField, IFieldsetBindingClient } from '../../../../types/template';
import { TaskRenderExtraFieldsInfo } from '../TaskRenderExtraFieldsInfo';

const makeField = (apiName: string) => makeExtraField({
  apiName,
  name: apiName,
});

const makeTask = (fields: IExtraField[], fieldsets: IFieldsetBindingClient[]) =>
  ({ fields, fieldsets } as any);

describe('TaskRenderExtraFieldsInfo', () => {
  it('does not render when fields are empty and fieldsets are empty', () => {
    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask([], []),
        onClick: jest.fn(),
      }),
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('does not render when fieldsets have no fields', () => {
    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask(
          [],
          [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', fields: [] })],
        ),
        onClick: jest.fn(),
      }),
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('counts only own fields when fieldsets have no fields', () => {
    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask(
          [makeField('field-1'), makeField('field-2')],
          [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', fields: [] })],
        ),
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('sums own fields and fieldset fields', () => {
    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask(
          [makeField('field-1')],
          [makeFieldsetBindingClient({
            apiNameBinding: 'fs-1',
            fields: [makeFieldsetField({ apiName: 'f-1' }), makeFieldsetField({ apiName: 'f-2' })],
          })],
        ),
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('sums fields from multiple fieldsets when task has no own fields', () => {
    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask(
          [],
          [
            makeFieldsetBindingClient({
              apiNameBinding: 'fs-1',
              fields: [makeFieldsetField({ apiName: 'f-1' }), makeFieldsetField({ apiName: 'f-2' })],
            }),
            makeFieldsetBindingClient({
              apiNameBinding: 'fs-2',
              fields: [
                makeFieldsetField({ apiName: 'f-3' }),
                makeFieldsetField({ apiName: 'f-4' }),
                makeFieldsetField({ apiName: 'f-5' }),
              ],
            }),
          ],
        ),
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toHaveTextContent('5');
  });

  it('recomputes counter when fieldsets prop changes', () => {
    const task = makeTask([], [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', fields: [] })]);

    const { rerender } = render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task,
        onClick: jest.fn(),
      }),
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();

    const updatedTask = makeTask([], [
      makeFieldsetBindingClient({
        apiNameBinding: 'fs-1',
        fields: [
          makeFieldsetField({ apiName: 'f-1' }),
          makeFieldsetField({ apiName: 'f-2' }),
          makeFieldsetField({ apiName: 'f-3' }),
          makeFieldsetField({ apiName: 'f-4' }),
        ],
      }),
    ]);

    rerender(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: updatedTask,
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toHaveTextContent('4');
  });
});
