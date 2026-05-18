// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { useSelector } from 'react-redux';

import { EExtraFieldType, IExtraField, ITaskFieldset } from '../../../../types/template';
import { TaskRenderExtraFieldsInfo } from '../TaskRenderExtraFieldsInfo';

const makeField = (apiName: string): IExtraField => ({
  apiName,
  name: apiName,
  type: EExtraFieldType.String,
  order: 0,
  isRequired: false,
  isHidden: false,
  userId: null,
  groupId: null,
  description: '',
  selections: [],
});

const makeTaskFieldset = (apiName: string): ITaskFieldset => ({ apiName, order: 0 });

const makeTask = (fields: IExtraField[], fieldsets: ITaskFieldset[]) =>
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
          [makeTaskFieldset('missing')],
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
          [makeTaskFieldset('fs-1')],
        ),
        onClick: jest.fn(),
      }),
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
