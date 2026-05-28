import * as React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import FieldsetDetails from '../FieldsetDetails';
import { intlMock } from '../../../../__stubs__/intlMock';
import { history } from '../../../../utils/history';
import { ERoutes } from '../../../../constants/routes';
import { TFieldsetDetailsProps } from '../types';
import {
  openEditModal,
  deleteFieldsetAction,
  loadCurrentFieldset,
  resetCurrentFieldset,
  updateFieldsetAction,
  setTemplateId,
} from '../../../../redux/fieldsets/slice';
import { ModifyDropdown, FilterSelect } from '../../../UI';
import { ExtraFieldIntl } from '../../../TemplateEdit/ExtraFields';
import { FieldsetModal } from '../../FieldsetModal/FieldsetModal';
import { getEmptyField } from '../../../TemplateEdit/KickoffRedux/utils/getEmptyField';
import { getEditedFields } from '../../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { moveWorkflowField } from '../../../../utils/workflows';
import { EExtraFieldType } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../../redux/fieldsets/slice', () => ({
  openEditModal: jest.fn(() => ({ type: 'fieldsets/openEditModal' })),
  deleteFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/deleteFieldsetAction', payload: p })),
  loadCurrentFieldset: jest.fn((p) => ({ type: 'fieldsets/loadCurrentFieldset', payload: p })),
  resetCurrentFieldset: jest.fn(() => ({ type: 'fieldsets/resetCurrentFieldset' })),
  updateFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/updateFieldsetAction', payload: p })),
  setTemplateId: jest.fn((p) => ({ type: 'fieldsets/setTemplateId', payload: p })),
}));

jest.mock('../../../UI', () => ({
  ModifyDropdown: jest.fn(() => null),
  Button: jest.fn((props: { label: string; onClick?: () => void; disabled?: boolean }) =>
    React.createElement('button', {
      onClick: props.onClick,
      disabled: props.disabled,
    }, props.label),
  ),
  FilterSelect: jest.fn((props: {
    options: { apiName: string; name: string }[];
    selectedOptions: (string | number | null)[];
    onChange: (vals: (string | number | null)[]) => void;
    renderPlaceholder?: (opts: { apiName: string; name: string }[]) => React.ReactNode;
  }) =>
    React.createElement(
      'div',
      { 'data-testid': 'filter-select' },
      React.createElement(
        'span',
        { 'data-testid': 'filter-placeholder' },
        props.renderPlaceholder ? props.renderPlaceholder(props.options) : null,
      ),
      ...props.options.map((opt) =>
        React.createElement(
          'button',
          {
            key: opt.apiName,
            type: 'button',
            'data-testid': `filter-option-${opt.apiName}`,
            onClick: () => {
              const isSelected = props.selectedOptions.includes(opt.apiName);
              const next = isSelected
                ? props.selectedOptions.filter((v) => v !== opt.apiName)
                : [...props.selectedOptions, opt.apiName];
              props.onChange(next);
            },
          },
          opt.name,
        ),
      ),
    ),
  ),
}));

jest.mock('../../../UI/ModifyDropdown/types', () => ({
  EModifyDropdownToggle: { Modify: 'modify' },
}));

jest.mock('../../FieldsetModal/FieldsetModal', () => ({
  FieldsetModal: jest.fn(() => null),
}));

jest.mock('../../FieldsetModal/types', () => ({
  EFieldsetModalType: { Edit: 'edit' },
}));

jest.mock('../FieldsetDetailsSkeleton', () => ({
  FieldsetDetailsSkeleton: jest.fn(() =>
    React.createElement('div', { role: 'status', 'aria-label': 'Loading' }),
  ),
}));

jest.mock('../../../TemplateEdit/ExtraFields', () => ({
  ExtraFieldIntl: jest.fn((props: { field: { apiName: string } }) =>
    React.createElement('div', { 'data-testid': `extra-field-${props.field.apiName}` }),
  ),
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/ExtraFieldsMap', () => ({
  ExtraFieldsMap: [{ id: 'string', title: 'Text' }],
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/ExtraFieldIcon', () => ({
  ExtraFieldIcon: jest.fn((props: { id: string; onClick: () => void }) =>
    React.createElement('button', {
      'data-testid': `field-icon-${props.id}`,
      onClick: props.onClick,
    }),
  ),
}));

jest.mock('../../../TemplateEdit/KickoffRedux/utils/getEmptyField', () => ({
  getEmptyField: jest.fn((type: string) => ({
    apiName: `new-${type}`,
    name: 'New Field',
    type,
    order: 0,
    userId: null,
    groupId: null,
  })),
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/getEditedFields', () => ({
  getEditedFields: jest.fn((fields: unknown[]) => fields),
}));

jest.mock('../../../../utils/workflows', () => ({
  getNormalizeFieldsOrders: jest.fn((f: unknown[]) => f),
  moveWorkflowField: jest.fn((_from: number, _to: number, fields: unknown[]) => fields),
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/useDatasetOptions', () => ({
  useDatasetOptions: jest.fn(() => []),
}));

jest.mock('../fieldsetFieldMappers', () => ({
  normalizeFieldsForUI: jest.fn((f: unknown[]) => f),
}));

describe('FieldsetDetails', () => {
  const mockDispatch = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const SAVE_SETTINGS_LABEL = formatMsg('fieldsets.save-settings');
  const SAVE_FIELDS_LABEL = formatMsg('fieldsets.save-fields');
  const SAVE_RULES_LABEL = formatMsg('fieldsets.save-rules');
  const UNSAVED_SETTINGS_HINT = formatMsg('fieldsets.unsaved-settings-changes');
  const UNSAVED_FIELDS_HINT = formatMsg('fieldsets.unsaved-changes');
  const UNSAVED_RULES_HINT = formatMsg('fieldsets.unsaved-rule-changes');
  const NO_FIELDS_TEXT = formatMsg('fieldsets.no-fields');
  const NO_RULES_TEXT = formatMsg('fieldsets.no-rules');
  const ADD_RULE_TEXT = formatMsg('fieldsets.add-rule');
  const RULE_DELETE_TEXT = formatMsg('fieldsets.rule-delete');

  const makeProps = (id: string = '10', templateId: string = '5'): TFieldsetDetailsProps => ({
    match: { params: { id, templateId }, isExact: true, path: '', url: '' },
    location: {
      pathname: `/templates/${templateId}/fieldsets/${id}/`,
      search: '',
      hash: '',
      state: undefined,
    },
    history: {
      ...history,
      length: 1,
      action: 'PUSH' as const,
      go: jest.fn(),
      goBack: jest.fn(),
      goForward: jest.fn(),
      replace: jest.fn(),
      block: jest.fn(),
      createHref: jest.fn(),
    },
  });

  const makeField = (overrides = {}) => ({
    apiName: `f-${Math.random().toString(36).slice(2, 6)}`,
    name: 'Field',
    type: EExtraFieldType.String,
    order: 0,
    userId: null,
    groupId: null,
    ...overrides,
  });

  const loadingState = {
    fieldsets: { currentFieldset: null, isCurrentFieldsetLoading: true },
    authUser: { account: { id: 1 } },
  };

  const nullFieldsetState = {
    fieldsets: { currentFieldset: null, isCurrentFieldsetLoading: false },
    authUser: { account: { id: 1 } },
  };

  const makeLoadedState = (fieldsetOverrides = {}) => {
    const fieldset = {
      id: 10,
      templateId: 5,
      name: 'Test Fieldset',
      description: '',
      labelPosition: EFieldLabelPosition.Top,
      layout: 'horizontal' as const,
      order: 0,
      kickoffId: null,
      taskId: null,
      rules: [],
      fields: [],
      ...fieldsetOverrides,
    };
    return {
      fieldsets: { currentFieldset: fieldset, isCurrentFieldsetLoading: false },
      authUser: { account: { id: 1 } },
    };
  };

  const getModifyDropdownProps = () => (ModifyDropdown as jest.Mock).mock.calls[0][0];
  const getFieldsetModalProps = () => (FieldsetModal as jest.Mock).mock.calls[0][0];
  const getExtraFieldIntlMock = () => ExtraFieldIntl as unknown as jest.Mock;
  const getUpdateActionMock = () => updateFieldsetAction as unknown as jest.Mock;
  const getFilterSelectMock = () => FilterSelect as unknown as jest.Mock;

  const renderWithState = (state: object, props = makeProps()) => {
    (useSelector as jest.Mock).mockImplementation((selector: (s: object) => unknown) => selector(state));
    return render(React.createElement(FieldsetDetails, props));
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockImplementation((selector: (s: object) => unknown) => selector(loadingState));
  });

  describe('URL parameter validation', () => {
    it('redirects to /templates/ on invalid templateId', () => {
      render(React.createElement(FieldsetDetails, makeProps('10', 'abc')));
      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(ERoutes.Templates);
      expect(setTemplateId).not.toHaveBeenCalled();
      expect(loadCurrentFieldset).not.toHaveBeenCalled();
    });

    it('redirects to fieldsets list on invalid id', () => {
      render(React.createElement(FieldsetDetails, makeProps('xyz', '5')));
      const expectedRoute = ERoutes.TemplateFieldsets.replace(':templateId', '5');
      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(expectedRoute);
    });

    it('dispatches setTemplateId and loadCurrentFieldset on valid params', () => {
      render(React.createElement(FieldsetDetails, makeProps('10', '5')));
      expect(history.push).not.toHaveBeenCalled();
      expect(mockDispatch).toHaveBeenCalledWith(setTemplateId(5));
      expect(mockDispatch).toHaveBeenCalledWith(loadCurrentFieldset({ id: 10 }));
    });
  });

  it('dispatches resetCurrentFieldset on unmount', () => {
    const { unmount } = render(React.createElement(FieldsetDetails, makeProps()));
    mockDispatch.mockClear();
    unmount();
    expect(mockDispatch).toHaveBeenCalledTimes(1);
    expect(mockDispatch).toHaveBeenCalledWith(resetCurrentFieldset());
  });

  describe('Loading state', () => {
    it('renders Skeleton when isLoading=true', () => {
      renderWithState(loadingState);
      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.queryByRole('heading', { level: 1 })).not.toBeInTheDocument();
    });

    it('renders nothing when fieldset=null and isLoading=false', () => {
      const { container } = renderWithState(nullFieldsetState);
      expect(container).toBeEmptyDOMElement();
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });
  });

  describe('Header and initialization', () => {
    it('displays fieldset name in heading', () => {
      renderWithState(makeLoadedState({ name: 'My Fieldset' }));
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent(/^My Fieldset$/);
    });

    it('onEdit in ModifyDropdown dispatches openEditModal', () => {
      renderWithState(makeLoadedState());
      const props = getModifyDropdownProps();
      act(() => { props.onEdit(); });
      expect(openEditModal).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(openEditModal());
    });

    it('onDelete in ModifyDropdown dispatches deleteFieldsetAction and redirects', () => {
      renderWithState(makeLoadedState({ id: 10 }), makeProps('10', '5'));
      const props = getModifyDropdownProps();
      act(() => { props.onDelete(); });
      expect(deleteFieldsetAction).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(deleteFieldsetAction({ id: 10 }));
      const expectedRoute = ERoutes.TemplateFieldsets.replace(':templateId', '5');
      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(expectedRoute);
    });

    it('skips loadCurrentFieldset when fieldset is already loaded with same id', () => {
      renderWithState(makeLoadedState({ id: 10 }), makeProps('10', '5'));
      expect(setTemplateId).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(setTemplateId(5));
      expect(loadCurrentFieldset).not.toHaveBeenCalled();
    });
  });

  describe('Initial save bar state', () => {
    it('no save bars are visible on initial render', () => {
      const fields = [makeField({ apiName: 'f1', order: 1 })];
      const rules = [{ id: 1, type: 'sum_equal', value: '100', fields: ['f1'] }];
      renderWithState(makeLoadedState({ fields, rules }));

      expect(screen.queryByText(UNSAVED_SETTINGS_HINT)).not.toBeInTheDocument();
      expect(screen.queryByText(UNSAVED_FIELDS_HINT)).not.toBeInTheDocument();
      expect(screen.queryByText(UNSAVED_RULES_HINT)).not.toBeInTheDocument();
    });
  });

  describe('Settings section', () => {
    it('syncs description and labelPosition from fieldset', () => {
      renderWithState(makeLoadedState({ description: 'Test desc', labelPosition: 'left' }));
      const textarea = screen.getByLabelText(formatMsg('fieldsets.settings.description'));
      const select = screen.getByLabelText(formatMsg('fieldsets.settings.label-position'));
      expect(textarea).toHaveValue('Test desc');
      expect(select).toHaveValue('left');
    });

    it('shows save bar after changing description', () => {
      renderWithState(makeLoadedState());
      const textarea = screen.getByLabelText(formatMsg('fieldsets.settings.description'));
      userEvent.type(textarea, 'new text');
      expect(screen.getByText(UNSAVED_SETTINGS_HINT)).toBeInTheDocument();
    });

    it('shows save bar after changing label position', () => {
      renderWithState(makeLoadedState());
      const select = screen.getByLabelText(formatMsg('fieldsets.settings.label-position'));
      userEvent.selectOptions(select, 'left');
      expect(screen.getByText(UNSAVED_SETTINGS_HINT)).toBeInTheDocument();
    });

    it('Save Settings dispatches updateFieldsetAction and hides save bar', () => {
      renderWithState(makeLoadedState({ id: 10 }));
      const textarea = screen.getByLabelText(formatMsg('fieldsets.settings.description'));
      userEvent.type(textarea, 'updated');

      userEvent.click(screen.getByRole('button', { name: SAVE_SETTINGS_LABEL }));

      expect(getUpdateActionMock()).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(
        updateFieldsetAction(expect.objectContaining({
          id: 10,
          description: 'updated',
          label_position: 'top',
        })),
      );
      expect(screen.queryByText(UNSAVED_SETTINGS_HINT)).not.toBeInTheDocument();
    });
  });

  describe('Fields section — display', () => {
    it('shows "No fields yet" when fields are empty', () => {
      renderWithState(makeLoadedState({ fields: [] }));
      expect(screen.getByText(NO_FIELDS_TEXT)).toBeInTheDocument();
    });

    it('renders ExtraFieldIntl for each field (order desc)', () => {
      const fields = [
        makeField({ apiName: 'f1', order: 1 }),
        makeField({ apiName: 'f2', order: 2 }),
      ];
      renderWithState(makeLoadedState({ fields }));

      expect(screen.getByTestId('extra-field-f1')).toBeInTheDocument();
      expect(screen.getByTestId('extra-field-f2')).toBeInTheDocument();

      const mock = getExtraFieldIntlMock();
      const fieldCalls = mock.mock.calls.filter(
        (c: unknown[]) => (c[0] as { field: { apiName: string } }).field.apiName.startsWith('f'),
      );
      expect(fieldCalls[0][0].field.apiName).toBe('f2');
      expect(fieldCalls[1][0].field.apiName).toBe('f1');
    });
  });

  describe('Fields section — CRUD', () => {
    it('handleCreateField adds a field and shows save bar', () => {
      renderWithState(makeLoadedState({ fields: [] }));

      userEvent.click(screen.getByTestId('field-icon-string'));

      expect(getEmptyField).toHaveBeenCalledTimes(1);
      expect(screen.getByText(UNSAVED_FIELDS_HINT)).toBeInTheDocument();
      expect(screen.getByTestId('extra-field-new-string')).toBeInTheDocument();
    });

    it('handleEditField calls getEditedFields with correct arguments', () => {
      const fields = [makeField({ apiName: 'f1', order: 1, name: 'Old' })];
      renderWithState(makeLoadedState({ fields }));

      const mock = getExtraFieldIntlMock();
      const editField = mock.mock.calls[mock.mock.calls.length - 1][0].editField;
      act(() => { editField({ name: 'New' }); });

      expect(getEditedFields).toHaveBeenCalledTimes(1);
      expect(getEditedFields).toHaveBeenCalledWith(
        expect.arrayContaining([expect.objectContaining({ apiName: 'f1' })]),
        'f1',
        { name: 'New' },
      );
    });

    it('handleDeleteField removes a field', () => {
      const fields = [
        makeField({ apiName: 'f1', order: 2 }),
        makeField({ apiName: 'f2', order: 1 }),
      ];
      renderWithState(makeLoadedState({ fields }));

      expect(screen.getByTestId('extra-field-f1')).toBeInTheDocument();
      expect(screen.getByTestId('extra-field-f2')).toBeInTheDocument();

      const mock = getExtraFieldIntlMock();
      const lastRenderCalls = mock.mock.calls.slice(-2);
      const deleteField = lastRenderCalls[0][0].deleteField;
      act(() => { deleteField(); });

      expect(screen.queryByTestId('extra-field-f1')).not.toBeInTheDocument();
      expect(screen.getByTestId('extra-field-f2')).toBeInTheDocument();
    });

    it('handleMoveField calls moveWorkflowField with correct arguments', () => {
      const fields = [
        makeField({ apiName: 'f1', order: 2 }),
        makeField({ apiName: 'f2', order: 1 }),
      ];
      renderWithState(makeLoadedState({ fields }));

      const mock = getExtraFieldIntlMock();
      const lastRenderCalls = mock.mock.calls.slice(-2);

      act(() => { lastRenderCalls[0][0].moveFieldDown(); });

      expect(moveWorkflowField).toHaveBeenCalledTimes(1);
      expect(moveWorkflowField).toHaveBeenCalledWith(
        0, 1, expect.arrayContaining([expect.objectContaining({ apiName: 'f1' })]),
      );
    });

    it('Save Fields dispatches updateFieldsetAction without id in fields', () => {
      renderWithState(makeLoadedState({ id: 10, fields: [] }));

      userEvent.click(screen.getByTestId('field-icon-string'));

      userEvent.click(screen.getByRole('button', { name: SAVE_FIELDS_LABEL }));

      expect(getUpdateActionMock()).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(
        updateFieldsetAction(expect.objectContaining({ id: 10 })),
      );

      const fieldsPayload = getUpdateActionMock().mock.calls[0][0].fields;
      expect(fieldsPayload).toBeDefined();
      fieldsPayload.forEach((field: Record<string, unknown>) => {
        expect(field).not.toHaveProperty('id');
      });

      expect(screen.queryByText(UNSAVED_FIELDS_HINT)).not.toBeInTheDocument();
    });
  });

  describe('Rules section — empty state', () => {
    it('shows "No rules yet" when rules are empty', () => {
      renderWithState(makeLoadedState({ rules: [] }));
      expect(screen.getByText(NO_RULES_TEXT)).toBeInTheDocument();
    });

    it('Add Rule button is always visible', () => {
      renderWithState(makeLoadedState());
      expect(screen.getByRole('button', { name: new RegExp(ADD_RULE_TEXT, 'i') })).toBeInTheDocument();
    });
  });

  describe('Rules section — CRUD', () => {
    it('handleAddRule adds a rule and shows save bar', () => {
      renderWithState(makeLoadedState());

      userEvent.click(screen.getByRole('button', { name: new RegExp(ADD_RULE_TEXT, 'i') }));

      expect(screen.getByText(UNSAVED_RULES_HINT)).toBeInTheDocument();
      const ruleInput = screen.getByPlaceholderText(formatMsg('fieldsets.rule-value-placeholder'));
      expect(ruleInput).toBeInTheDocument();
    });

    it('handleEditRuleValue updates rule value', () => {
      renderWithState(makeLoadedState());

      userEvent.click(screen.getByRole('button', { name: new RegExp(ADD_RULE_TEXT, 'i') }));

      const ruleInput = screen.getByPlaceholderText(formatMsg('fieldsets.rule-value-placeholder'));
      userEvent.type(ruleInput, '100');
      expect(ruleInput).toHaveValue('100');
    });

    it('handleDeleteRule removes a rule', () => {
      renderWithState(makeLoadedState());

      userEvent.click(screen.getByRole('button', { name: new RegExp(ADD_RULE_TEXT, 'i') }));
      expect(screen.getByPlaceholderText(formatMsg('fieldsets.rule-value-placeholder'))).toBeInTheDocument();

      userEvent.click(screen.getByText(RULE_DELETE_TEXT));
      expect(screen.queryByPlaceholderText(formatMsg('fieldsets.rule-value-placeholder'))).not.toBeInTheDocument();
    });

    it('Save Rules end-to-end: add, edit fields, save, verify payload', () => {
      const fields = [
        makeField({ apiName: 'field-1', order: 1 }),
        makeField({ apiName: 'field-2', order: 2 }),
      ];
      renderWithState(makeLoadedState({ id: 10, fields }));

      userEvent.click(screen.getByRole('button', { name: new RegExp(ADD_RULE_TEXT, 'i') }));

      const filterMock = getFilterSelectMock();
      const lastFilterCall = filterMock.mock.calls[filterMock.mock.calls.length - 1];
      const onChange = lastFilterCall[0].onChange;

      act(() => { onChange(['field-1', null, 42, 'field-2']); });

      userEvent.click(screen.getByRole('button', { name: SAVE_RULES_LABEL }));

      expect(getUpdateActionMock()).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(
        updateFieldsetAction(expect.objectContaining({
          id: 10,
          rules: expect.arrayContaining([
            expect.objectContaining({
              type: 'sum_equal',
              fields: ['field-1', 'field-2'],
            }),
          ]),
        })),
      );

      const rulesPayload = getUpdateActionMock().mock.calls[0][0].rules;
      expect(rulesPayload[0].id).toBeUndefined();

      expect(screen.queryByText(UNSAVED_RULES_HINT)).not.toBeInTheDocument();
    });
  });

  describe('FieldsetModal', () => {
    it('renders FieldsetModal with type=Edit', () => {
      renderWithState(makeLoadedState());
      const props = getFieldsetModalProps();
      expect(props.type).toBe('edit');
    });
  });

  describe('External rules sync', () => {
    it('re-syncs local rules from store and hides save bar on external fieldset update', () => {
      const initialState = makeLoadedState({
        id: 10,
        rules: [{ id: 1, type: 'sum_equal', value: 'old', fields: [] }],
      });
      (useSelector as jest.Mock).mockImplementation((selector: (s: object) => unknown) =>
        selector(initialState),
      );
      const { rerender } = render(React.createElement(FieldsetDetails, makeProps()));

      const ruleInput = screen.getByPlaceholderText(formatMsg('fieldsets.rule-value-placeholder'));
      userEvent.type(ruleInput, '!');
      expect(ruleInput).toHaveValue('old!');
      expect(screen.getByText(UNSAVED_RULES_HINT)).toBeInTheDocument();

      const updatedState = makeLoadedState({
        id: 10,
        rules: [{ id: 2, type: 'sum_equal', value: 'fresh', fields: [] }],
      });
      (useSelector as jest.Mock).mockImplementation((selector: (s: object) => unknown) =>
        selector(updatedState),
      );
      rerender(React.createElement(FieldsetDetails, makeProps()));

      expect(screen.queryByDisplayValue('old!')).not.toBeInTheDocument();
      expect(screen.getByDisplayValue('fresh')).toBeInTheDocument();
      expect(screen.queryByText(UNSAVED_RULES_HINT)).not.toBeInTheDocument();
      expect(mockDispatch).not.toHaveBeenCalledWith(
        expect.objectContaining({ type: 'fieldsets/updateFieldsetAction' }),
      );
    });
  });

  describe('Selected fields placeholder in FilterSelect', () => {
    it('shows selected field names joined by comma after picking fields in UI', () => {
      const fields = [
        makeField({ apiName: 'field-1', name: 'Total', order: 1 }),
        makeField({ apiName: 'field-2', name: 'Tax', order: 2 }),
        makeField({ apiName: 'field-3', name: 'Discount', order: 3 }),
      ];
      renderWithState(makeLoadedState({ id: 10, fields }));

      userEvent.click(screen.getByRole('button', { name: new RegExp(ADD_RULE_TEXT, 'i') }));

      expect(screen.getByTestId('filter-placeholder'))
        .toHaveTextContent(formatMsg('fieldsets.rule-fields-placeholder'));

      userEvent.click(screen.getByTestId('filter-option-field-1'));
      userEvent.click(screen.getByTestId('filter-option-field-3'));

      expect(screen.getByTestId('filter-placeholder')).toHaveTextContent(/^Total, Discount$/);
    });
  });
});
