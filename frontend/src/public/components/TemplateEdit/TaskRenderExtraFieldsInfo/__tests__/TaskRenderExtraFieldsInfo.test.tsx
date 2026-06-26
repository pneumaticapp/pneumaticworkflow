import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useSelector } from 'react-redux';

import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetBindingClient } from '../../../../__stubs__/fieldsets.factory';
import { IExtraField, IFieldsetBindingClient } from '../../../../types/template';
import { TaskRenderExtraFieldsInfo } from '../TaskRenderExtraFieldsInfo';

const makeField = (apiName: string) => makeExtraField({
  apiName,
  name: apiName,
});

const makeTask = (fields: IExtraField[], fieldsets: IFieldsetBindingClient[]) =>
  ({ fields, fieldsets } as any);

const makeFieldsetsMap = (entries: [string, number][]) =>
  new Map(entries.map(([apiName, fieldsCount]) => [
    apiName,
    { fields: Array.from({ length: fieldsCount }, (_, i) => ({ apiName: `f-${apiName}-${i}` })) },
  ]));

describe('TaskRenderExtraFieldsInfo', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does not render when fields are empty and fieldsets are empty', () => {
    (useSelector as jest.Mock).mockReturnValue(new Map());

    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask([], []),
        onClick: jest.fn(),
      }),
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('counts only own fields when fieldset is absent from catalog', () => {
    (useSelector as jest.Mock).mockReturnValue(makeFieldsetsMap([]));

    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask(
          [makeField('field-1'), makeField('field-2')],
          [makeFieldsetBindingClient({ apiNameBinding: 'missing' })],
        ),
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('sums own fields and fieldset fields from catalog', () => {
    (useSelector as jest.Mock).mockReturnValue(makeFieldsetsMap([['fs-1', 2]]));

    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask(
          [makeField('field-1')],
          [makeFieldsetBindingClient({ apiNameBinding: 'fs-1' })],
        ),
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('sums fields from multiple fieldsets when task has no own fields', () => {
    (useSelector as jest.Mock).mockReturnValue(
      makeFieldsetsMap([
        ['fs-1', 2],
        ['fs-2', 3],
      ]),
    );

    render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task: makeTask(
          [],
          [makeFieldsetBindingClient({ apiNameBinding: 'fs-1' }), makeFieldsetBindingClient({ apiNameBinding: 'fs-2' })],
        ),
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toHaveTextContent('5');
  });

  it('recomputes counter when fieldsets catalog is updated', () => {
    (useSelector as jest.Mock).mockReturnValue(new Map());

    const task = makeTask([], [makeFieldsetBindingClient({ apiNameBinding: 'fs-1' })]);

    const { rerender } = render(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task,
        onClick: jest.fn(),
      }),
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();

    (useSelector as jest.Mock).mockReturnValue(makeFieldsetsMap([['fs-1', 4]]));

    rerender(
      React.createElement(TaskRenderExtraFieldsInfo as React.FC<any>, {
        task,
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toHaveTextContent('4');
  });
});
