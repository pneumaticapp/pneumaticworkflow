import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { intlMock } from '../../../../__stubs__/intlMock';
import {
  EExtraFieldType,
  IExtraField,
  IFieldsetData,
  ITemplateTask,
} from '../../../../types/template';

jest.mock('../../ExtraFields/utils/useDatasetOptions', () => ({
  useDatasetOptions: jest.fn(() => []),
}));

jest.mock('../../KickoffRedux/utils/getEmptyField', () => ({
  getEmptyField: jest.fn(),
}));

jest.mock('../../ExtraFields/utils/ExtraFieldsMap', () => ({
  ExtraFieldsMap: [{ id: 'string', label: 'String' }],
}));

jest.mock('../../ExtraFields/utils/ExtraFieldIcon', () => ({
  ExtraFieldIcon: (props: { id: string; onClick: () => void }) =>
    React.createElement(
      'button',
      { type: 'button', onClick: props.onClick },
      `Add field ${props.id}`,
    ),
}));

jest.mock('../../TaskOutputFlow/FieldsetIconPicker', () => ({
  FieldsetIconPicker: (props: {
    fieldsetsByApiName: ReadonlyMap<string, IFieldsetData>;
    selectedFieldsetApiNames: string[];
    onSelectFieldset: (apiName: string) => void;
    onRemoveFieldset: (apiName: string) => void;
  }) =>
    React.createElement(
      'div',
      null,
      Array.from(props.fieldsetsByApiName.entries()).map(([apiName, fs]) =>
        React.createElement(
          'button',
          {
            key: `add-${apiName}`,
            type: 'button',
            onClick: () => props.onSelectFieldset(apiName),
          },
          `Add fieldset ${fs.name}`,
        ),
      ),
      props.selectedFieldsetApiNames.map((apiName) =>
        React.createElement(
          'button',
          {
            key: `remove-${apiName}`,
            type: 'button',
            onClick: () => props.onRemoveFieldset(apiName),
          },
          `Remove fieldset ${apiName}`,
        ),
      ),
    ),
}));

jest.mock('../../TaskOutputFlow/MergedOutputRows', () => ({
  MergedOutputRows: (props: {
    mergedRows: Array<
      | { kind: 'field'; field: IExtraField }
      | { kind: 'fieldset'; apiName: string; order: number }
    >;
    onDeleteField: (apiName: string) => void;
    onMoveRow: (index: number, direction: 'up' | 'down') => void;
    onEditField: (apiName: string) => (changed: Partial<IExtraField>) => void;
    onRemoveFieldset: (apiName: string) => void;
  }) =>
    React.createElement(
      'div',
      { 'data-testid': 'merged-rows' },
      props.mergedRows.map((row, index) => {
        if (row.kind === 'field') {
          const apiName = row.field.apiName;
          return React.createElement(
            'div',
            { key: `field-${apiName}` },
            React.createElement(
              'button',
              { type: 'button', onClick: () => props.onDeleteField(apiName) },
              `Delete ${apiName}`,
            ),
            React.createElement(
              'button',
              {
                type: 'button',
                onClick: () => props.onEditField(apiName)({ name: 'EditedName' }),
              },
              `Edit ${apiName}`,
            ),
            React.createElement(
              'button',
              { type: 'button', onClick: () => props.onMoveRow(index, 'up') },
              `Move row ${index} up`,
            ),
            React.createElement(
              'button',
              { type: 'button', onClick: () => props.onMoveRow(index, 'down') },
              `Move row ${index} down`,
            ),
          );
        }
        return React.createElement(
          'div',
          { key: `fieldset-${row.apiName}` },
          React.createElement(
            'button',
            { type: 'button', onClick: () => props.onMoveRow(index, 'up') },
            `Move row ${index} up`,
          ),
          React.createElement(
            'button',
            { type: 'button', onClick: () => props.onMoveRow(index, 'down') },
            `Move row ${index} down`,
          ),
        );
      }),
    ),
}));

import { OutputFormTaskMerged } from '../OutputFormTaskMerged';
import { getEmptyField } from '../../KickoffRedux/utils/getEmptyField';

describe('OutputFormTaskMerged', () => {
  const makeTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask => ({
    id: 1,
    apiName: 'task-1',
    name: 'Task',
    description: '',
    number: 1,
    rawPerformers: [],
    requireCompletionByAll: false,
    skipForStarter: false,
    fields: [],
    fieldsets: [],
    delay: null,
    rawDueDate: null as any,
    conditions: [],
    uuid: 'task-uuid',
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  });

  const makeField = (overrides: Partial<IExtraField> = {}): IExtraField => ({
    apiName: 'f-1',
    name: 'Field 1',
    type: EExtraFieldType.String,
    order: 0,
    isRequired: false,
    isHidden: false,
    userId: null,
    groupId: null,
    description: '',
    selections: [],
    ...overrides,
  });

  const makeFieldsetData = (overrides: Partial<IFieldsetData> = {}): IFieldsetData => ({
    id: 1,
    apiName: 'fs-1',
    name: 'Fieldset 1',
    description: '',
    order: 0,
    fields: [],
    ...overrides,
  });

  const NEW_FIELD: IExtraField = {
    apiName: 'new-field',
    name: 'New Field',
    type: EExtraFieldType.String,
    order: -1,
    isRequired: false,
    isHidden: false,
    userId: null,
    groupId: null,
    description: '',
    selections: [],
  };

  const renderForm = (props: {
    task: ITemplateTask;
    fieldsetsByApiName?: ReadonlyMap<string, IFieldsetData>;
    patchTask?: jest.Mock;
  }) => {
    const patchTask = props.patchTask ?? jest.fn();
    const fieldsetsByApiName = props.fieldsetsByApiName ?? new Map<string, IFieldsetData>();
    render(
      React.createElement(OutputFormTaskMerged, {
        task: props.task,
        fieldsetsByApiName,
        fieldsetsCatalogLoading: false,
        templateId: 1,
        accountId: 1,
        patchTask,
        intl: intlMock,
      } as React.ComponentProps<typeof OutputFormTaskMerged>),
    );
    return { patchTask };
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (getEmptyField as jest.Mock).mockReturnValue(NEW_FIELD);
  });

  describe('rows table visibility', () => {
    it('does not render rows table when there are no fields and no fieldsets', () => {
      renderForm({ task: makeTask({ fields: [], fieldsets: [] }) });
      expect(screen.queryByTestId('merged-rows')).not.toBeInTheDocument();
    });

    it('renders rows table when there are fieldsets but no own fields', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-1' });
      renderForm({
        task: makeTask({ fields: [], fieldsets: [{ apiName: 'fs-1', order: 0 }] }),
        fieldsetsByApiName: new Map([['fs-1', fsData]]),
      });
      expect(screen.getByTestId('merged-rows')).toBeInTheDocument();
    });
  });

  describe('field actions', () => {
    it('adding a field sends PATCH with new field and fieldset order recalculated', () => {
      const existingField = makeField({ apiName: 'f-1', order: 0 });
      const { patchTask } = renderForm({
        task: makeTask({
          fields: [existingField],
          fieldsets: [{ apiName: 'fs-1', order: 1 }],
        }),
        fieldsetsByApiName: new Map([['fs-1', makeFieldsetData()]]),
      });

      userEvent.click(screen.getByRole('button', { name: 'Add field string' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      expect(arg.taskUUID).toBe('task-uuid');
      expect(arg.changedFields.fields).toBeDefined();
      expect(arg.changedFields.fieldsets).toBeDefined();
      const fieldApiNames = arg.changedFields.fields.map((f: IExtraField) => f.apiName);
      expect(fieldApiNames).toContain('new-field');
      expect(fieldApiNames).toContain('f-1');
      const patchApiNames = arg.changedFields.fieldsets.map((p: { apiName: string }) => p.apiName);
      expect(patchApiNames).toContain('fs-1');
    });

    it('editing a field sends PATCH with fields only, without fieldsets payload', () => {
      const existingField = makeField({ apiName: 'f-1', name: 'Old' });
      const { patchTask } = renderForm({
        task: makeTask({
          fields: [existingField],
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
        }),
        fieldsetsByApiName: new Map([['fs-1', makeFieldsetData()]]),
      });

      userEvent.click(screen.getByRole('button', { name: 'Edit f-1' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      expect(arg.changedFields.fields).toBeDefined();
      expect(arg.changedFields.fieldsets).toBeUndefined();
    });

    it('deleting a field sends PATCH without that field and recomputes order including fieldsets', () => {
      const fieldA = makeField({ apiName: 'f-a', order: 1 });
      const fieldB = makeField({ apiName: 'f-b', order: 2 });
      const { patchTask } = renderForm({
        task: makeTask({
          fields: [fieldA, fieldB],
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
        }),
        fieldsetsByApiName: new Map([['fs-1', makeFieldsetData()]]),
      });

      userEvent.click(screen.getByRole('button', { name: 'Delete f-a' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      const fieldApiNames = arg.changedFields.fields.map((f: IExtraField) => f.apiName);
      expect(fieldApiNames).not.toContain('f-a');
      expect(fieldApiNames).toContain('f-b');
      expect(arg.changedFields.fieldsets).toBeDefined();
      const patchApiNames = arg.changedFields.fieldsets.map((p: { apiName: string }) => p.apiName);
      expect(patchApiNames).toContain('fs-1');
    });
  });

  describe('fieldset actions', () => {
    it('adding a fieldset sends PATCH with both fields and fieldset patches', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-new', name: 'New Set' });
      const existingField = makeField({ apiName: 'f-1' });
      const { patchTask } = renderForm({
        task: makeTask({ fields: [existingField], fieldsets: [] }),
        fieldsetsByApiName: new Map([['fs-new', fsData]]),
      });

      userEvent.click(screen.getByRole('button', { name: 'Add fieldset New Set' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      expect(arg.changedFields.fields).toBeDefined();
      expect(arg.changedFields.fieldsets).toBeDefined();
      const patchApiNames = arg.changedFields.fieldsets.map((p: { apiName: string }) => p.apiName);
      expect(patchApiNames).toContain('fs-new');
    });

    it('does not send PATCH when adding an already-connected fieldset', () => {
      const fsData = makeFieldsetData({ apiName: 'fs-1' });
      const { patchTask } = renderForm({
        task: makeTask({ fields: [], fieldsets: [{ apiName: 'fs-1', order: 0 }] }),
        fieldsetsByApiName: new Map([['fs-1', fsData]]),
      });

      userEvent.click(screen.getByRole('button', { name: 'Add fieldset Fieldset 1' }));

      expect(patchTask).not.toHaveBeenCalled();
    });

    it('removing a fieldset sends PATCH without it and recomputes order of remaining ones', () => {
      const fsA = makeFieldsetData({ apiName: 'fs-a' });
      const fsB = makeFieldsetData({ apiName: 'fs-b' });
      const { patchTask } = renderForm({
        task: makeTask({
          fields: [],
          fieldsets: [
            { apiName: 'fs-a', order: 0 },
            { apiName: 'fs-b', order: 1 },
          ],
        }),
        fieldsetsByApiName: new Map([
          ['fs-a', fsA],
          ['fs-b', fsB],
        ]),
      });

      userEvent.click(screen.getByRole('button', { name: 'Remove fieldset fs-a' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      expect(arg.changedFields.fieldsets).toBeDefined();
      const patchApiNames = arg.changedFields.fieldsets.map((p: { apiName: string }) => p.apiName);
      expect(patchApiNames).not.toContain('fs-a');
      expect(patchApiNames).toContain('fs-b');
    });
  });

  describe('merged rows reordering', () => {
    it('reordering a row sends PATCH with both updated fields and fieldset patches', () => {
      const fieldA = makeField({ apiName: 'f-a', order: 1 });
      const fsData = makeFieldsetData({ apiName: 'fs-1' });
      const { patchTask } = renderForm({
        task: makeTask({
          fields: [fieldA],
          fieldsets: [{ apiName: 'fs-1', order: 0 }],
        }),
        fieldsetsByApiName: new Map([['fs-1', fsData]]),
      });

      userEvent.click(screen.getByRole('button', { name: 'Move row 0 down' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      expect(arg.changedFields.fields).toBeDefined();
      expect(arg.changedFields.fieldsets).toBeDefined();
      const field = arg.changedFields.fields.find((f: IExtraField) => f.apiName === 'f-a');
      expect(field).toBeDefined();
      const fsPatch = arg.changedFields.fieldsets.find((p: { apiName: string }) => p.apiName === 'fs-1');
      expect(fsPatch).toBeDefined();
      expect(fsPatch.order).toBe(1);
      expect(field.order).toBe(0);
    });
  });
});
