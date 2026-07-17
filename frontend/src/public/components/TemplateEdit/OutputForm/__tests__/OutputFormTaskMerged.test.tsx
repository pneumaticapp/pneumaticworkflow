import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { intlMock } from '../../../../__stubs__/intlMock';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { makeFieldsetBindingClient, makeFieldsetCatalogItem } from '../../../../__stubs__/fieldsets.factory';
import { makeTemplateTaskClient } from '../../../../__stubs__/templates.factory';
import {
  IExtraField,
  ITemplateTaskClient,
} from '../../../../types/template';
import { IFieldsetCatalogItem } from '../../../../types/fieldset';

jest.mock('../../../../redux/selectors/fieldsets', () => ({
  getFieldsetsCatalogItems: jest.fn(() => []),
}));

import { getFieldsetsCatalogItems } from '../../../../redux/selectors/fieldsets';

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
    selectedFieldsetIds: number[];
    onSelectFieldset: (item: IFieldsetCatalogItem) => void;
    onRemoveFieldset: (sharedFieldsetId: number) => void;
  }) => {
    const catalogItems = (getFieldsetsCatalogItems as jest.Mock)();
    return React.createElement(
      'div',
      null,
      catalogItems.map((item: IFieldsetCatalogItem) =>
        React.createElement(
          'button',
          {
            key: `add-${item.id}`,
            type: 'button',
            onClick: () => props.onSelectFieldset(item),
          },
          `Add fieldset ${item.name}`,
        ),
      ),
      props.selectedFieldsetIds.map((id: number) =>
        React.createElement(
          'button',
          {
            key: `remove-${id}`,
            type: 'button',
            onClick: () => props.onRemoveFieldset(id),
          },
          `Remove fieldset ${id}`,
        ),
      ),
    );
  },
}));

jest.mock('../../TaskOutputFlow/MergedOutputRows', () => ({
  MergedOutputRows: (props: {
    mergedRows: Array<
      | { kind: 'field'; field: IExtraField }
      | { kind: 'fieldset'; apiName?: string; order: number; sharedFieldsetId?: number }
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
          { key: `fieldset-${row.apiName ?? row.sharedFieldsetId ?? index}` },
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
  const makeTask = makeTemplateTaskClient;

  const makeField = (overrides: Partial<IExtraField> = {}) => makeExtraField({
    name: 'Field 1',
    ...overrides,
  });

  const NEW_FIELD: IExtraField = makeExtraField({
    apiName: 'new-field',
    name: 'New Field',
    order: -1,
  });

  const renderForm = (props: {
    task: ITemplateTaskClient;
    catalogItems?: IFieldsetCatalogItem[];
    patchTask?: jest.Mock;
  }) => {
    const patchTask = props.patchTask ?? jest.fn();
    const catalogItems = props.catalogItems ?? [];
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue(catalogItems);

    render(
      React.createElement(OutputFormTaskMerged, {
        task: props.task,
        fieldsetsCatalogLoading: false,
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
    (getFieldsetsCatalogItems as jest.Mock).mockReturnValue([]);
  });

  describe('rows table visibility', () => {
    it('does not render rows table when there are no fields and no fieldsets', () => {
      renderForm({ task: makeTask({ fields: [], fieldsets: [] }) });
      expect(screen.queryByTestId('merged-rows')).not.toBeInTheDocument();
    });

    it('renders rows table when there are fieldsets but no own fields', () => {
      renderForm({
        task: makeTask({ fields: [], fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0 })] }),
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
          fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 1 })],
        }),
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
      const patchBindingNames = arg.changedFields.fieldsets.map((p: { apiNameBinding: string }) => p.apiNameBinding);
      expect(patchBindingNames).toContain('fs-1');
    });

    it('editing a field sends PATCH with fields only, without fieldsets payload', () => {
      const existingField = makeField({ apiName: 'f-1', name: 'Old' });
      const { patchTask } = renderForm({
        task: makeTask({
          fields: [existingField],
          fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0 })],
        }),
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
          fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0 })],
        }),
      });

      userEvent.click(screen.getByRole('button', { name: 'Delete f-a' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      const fieldApiNames = arg.changedFields.fields.map((f: IExtraField) => f.apiName);
      expect(fieldApiNames).not.toContain('f-a');
      expect(fieldApiNames).toContain('f-b');
      expect(arg.changedFields.fieldsets).toBeDefined();
      const patchBindingNames = arg.changedFields.fieldsets.map((p: { apiNameBinding: string }) => p.apiNameBinding);
      expect(patchBindingNames).toContain('fs-1');
    });
  });

  describe('fieldset actions', () => {
    it('adding a fieldset sends PATCH with both fields and fieldset patches', () => {
      const catalogItem = makeFieldsetCatalogItem({ id: 99, apiName: 'fs-new', name: 'New Set' });
      const existingField = makeField({ apiName: 'f-1' });
      const { patchTask } = renderForm({
        task: makeTask({ fields: [existingField], fieldsets: [] }),
        catalogItems: [catalogItem],
      });

      userEvent.click(screen.getByRole('button', { name: 'Add fieldset New Set' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      expect(arg.changedFields.fields).toBeDefined();
      expect(arg.changedFields.fieldsets).toBeDefined();
    });

    it('does not send PATCH when adding an already-connected fieldset', () => {
      const catalogItem = makeFieldsetCatalogItem({ id: 1, apiName: 'fs-1', name: 'Fieldset 1' });
      const { patchTask } = renderForm({
        task: makeTask({ fields: [], fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0, sharedFieldsetId: 1 })] }),
        catalogItems: [catalogItem],
      });

      userEvent.click(screen.getByRole('button', { name: 'Add fieldset Fieldset 1' }));

      expect(patchTask).not.toHaveBeenCalled();
    });

    it('removing a fieldset sends PATCH without it and recomputes order of remaining ones', () => {
      const { patchTask } = renderForm({
        task: makeTask({
          fields: [],
          fieldsets: [
             makeFieldsetBindingClient({ apiNameBinding: 'fs-a', order: 0, sharedFieldsetId: 10 }),
            makeFieldsetBindingClient({ apiNameBinding: 'fs-b', order: 1, sharedFieldsetId: 20 }),
          ],
        }),
      });

      userEvent.click(screen.getByRole('button', { name: 'Remove fieldset 10' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      expect(arg.changedFields.fieldsets).toBeDefined();
      const patchBindingNames = arg.changedFields.fieldsets.map((p: { apiNameBinding: string }) => p.apiNameBinding);
      expect(patchBindingNames).not.toContain('fs-a');
      expect(patchBindingNames).toContain('fs-b');
    });
  });

  describe('merged rows reordering', () => {
    it('reordering a row sends PATCH with both updated fields and fieldset patches', () => {
      const fieldA = makeField({ apiName: 'f-a', order: 1 });
      const { patchTask } = renderForm({
        task: makeTask({
          fields: [fieldA],
          fieldsets: [makeFieldsetBindingClient({ apiNameBinding: 'fs-1', order: 0 })],
        }),
      });

      userEvent.click(screen.getByRole('button', { name: 'Move row 0 down' }));

      expect(patchTask).toHaveBeenCalledTimes(1);
      const arg = patchTask.mock.calls[0][0];
      expect(arg.changedFields.fields).toBeDefined();
      expect(arg.changedFields.fieldsets).toBeDefined();
      const field = arg.changedFields.fields.find((f: IExtraField) => f.apiName === 'f-a');
      expect(field).toBeDefined();
      const fsPatch = arg.changedFields.fieldsets.find((p: { apiNameBinding: string }) => p.apiNameBinding === 'fs-1');
      expect(fsPatch).toBeDefined();
      expect(fsPatch.order).toBe(1);
      expect(field.order).toBe(0);
    });
  });
});
