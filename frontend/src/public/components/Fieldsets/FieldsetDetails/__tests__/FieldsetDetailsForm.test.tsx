import React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { FieldsetDetailsForm } from '../FieldsetDetailsForm';
import { intlMock } from '../../../../__stubs__/intlMock';
import { openEditModal, deleteFieldsetAction } from '../../../../redux/fieldsets/slice';
import { ModifyDropdown } from '../../../UI';
import { EExtraFieldType } from '../../../../types/template';
import { EFieldLabelPosition } from '../../../../types/fieldset';
import type { IFieldsetCatalogItem } from '../../../../types/fieldset';
import {
  makeFieldsetCatalogItem,
  makeFieldsetField,
  makeFieldsetRuleset,
} from '../../../../__stubs__/fieldsets.factory';
import { FieldsetSettings } from '../FieldsetSettings/FieldsetSettings';
import { FieldsetFieldsList } from '../FieldsetFieldsList/FieldsetFieldsList';
import { FieldsetRulesetsList } from '../FieldsetRulesetsList/FieldsetRulesetsList';
import { saveFieldset, cloneFieldset } from '../utils';

jest.mock('../utils', () => ({
  ...jest.requireActual('../utils'),
  saveFieldset: jest.fn(),
  cloneFieldset: jest.fn(),
}));

jest.mock('../../../../utils/history', () => ({
  history: {
    push: jest.fn(),
  },
}));

jest.mock('../../../../redux/fieldsets/slice', () => ({
  openEditModal: jest.fn(() => ({ type: 'fieldsets/openEditModal' })),
  deleteFieldsetAction: jest.fn((payload) => ({ type: 'fieldsets/deleteFieldsetAction', payload })),
}));

jest.mock('../../../../redux/selectors/user', () => ({
  getAccountId: jest.fn(() => 1),
}));

jest.mock('../../../UI', () => ({
  ModifyDropdown: jest.fn((properties: { onClone?: () => void }) =>
    React.createElement(
      'div',
      null,
      React.createElement('button', { 'data-testid': 'modify-clone', onClick: properties.onClone }),
    ),
  ),
  Button: jest.fn((properties: { label: string; onClick?: () => void; disabled?: boolean }) =>
    React.createElement('button', { onClick: properties.onClick, disabled: properties.disabled }, properties.label),
  ),
}));

jest.mock('../../FieldsetModal/FieldsetModal', () => ({
  FieldsetModal: jest.fn(() => null),
}));

jest.mock('../FieldsetUnsavedChangesModal', () => ({
  FieldsetUnsavedChangesModal: jest.fn(() => null),
}));

jest.mock('../FieldRuleModal', () => ({
  FieldRuleModal: jest.fn((properties: { isOpen: boolean }) =>
    properties.isOpen ? React.createElement('div', { 'data-testid': 'field-rule-modal' }) : null,
  ),
}));

jest.mock('../FieldsetUsageBanner/FieldsetUsageBanner', () => ({
  FieldsetUsageBanner: jest.fn(() => null),
}));

jest.mock('../FieldsetSettings/FieldsetSettings', () => ({
  FieldsetSettings: jest.fn(() => null),
}));

jest.mock('../FieldsetFieldsList/FieldsetFieldsList', () => ({
  FieldsetFieldsList: jest.fn(() => null),
}));

jest.mock('../FieldsetRulesetsList/FieldsetRulesetsList', () => ({
  FieldsetRulesetsList: jest.fn(() => null),
}));

jest.mock('../../../TemplateEdit/ExtraFields/utils/useDatasetOptions', () => ({
  useDatasetOptions: jest.fn(() => []),
}));

describe('FieldsetDetailsForm', () => {
  const mockDispatch = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const SAVE_LABEL = formatMsg('fieldsets.save');
  const UNSAVED_HINT = formatMsg('fieldsets.unsaved-changes');

  const makeFieldset = (overrides: Partial<IFieldsetCatalogItem> = {}): IFieldsetCatalogItem =>
    makeFieldsetCatalogItem({
      id: 10,
      layout: 'horizontal',
      ...overrides,
    });

  const getModifyDropdownProps = () => (ModifyDropdown as jest.Mock).mock.calls[0][0];
  const getFieldsetSettingsProps = () => {
    const calls = (FieldsetSettings as jest.Mock).mock.calls;
    return calls[calls.length - 1][0];
  };
  const getFieldsetFieldsListProps = () => {
    const calls = (FieldsetFieldsList as jest.Mock).mock.calls;
    return calls[calls.length - 1][0];
  };
  const getFieldsetRulesetsListProps = () => {
    const calls = (FieldsetRulesetsList as jest.Mock).mock.calls;
    return calls[calls.length - 1][0];
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
    (useSelector as jest.Mock).mockImplementation((selector: () => unknown) => selector());
  });

  describe('Header and initialization', () => {
    it('displays fieldset name in heading', () => {
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ name: 'My Fieldset' }) }));
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent(/^My Fieldset$/);
    });

    it('onEdit in ModifyDropdown dispatches openEditModal', () => {
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset() }));
      getModifyDropdownProps().onEdit();
      expect(openEditModal).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(openEditModal());
    });

    it('onDelete in ModifyDropdown dispatches deleteFieldsetAction with onSuccess callback', () => {
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ id: 10 }) }));
      getModifyDropdownProps().onDelete();
      expect(deleteFieldsetAction).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(
        deleteFieldsetAction(
          expect.objectContaining({
            id: 10,
            onSuccess: expect.any(Function),
          }),
        ),
      );
    });

    it('onClone in ModifyDropdown calls cloneFieldset and passes cloneLabel', () => {
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ id: 10 }) }));
      const properties = getModifyDropdownProps();

      expect(properties.cloneLabel).toBe(formatMsg('fieldsets.clone'));

      properties.onClone();
      expect(cloneFieldset).toHaveBeenCalledTimes(1);
      expect(cloneFieldset).toHaveBeenCalledWith(expect.objectContaining({ fieldsetId: 10 }));
    });
  });

  describe('Initial save bar state', () => {
    it('shows disabled Save button on initial render', () => {
      const fields = [makeFieldsetField({ apiName: 'f1', order: 1 })];
      const rulesets = [makeFieldsetRuleset({ apiName: 'rule-1', fields: ['f1'] })];
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ fields, rulesets }) }));

      const saveButton = screen.getByRole('button', { name: SAVE_LABEL });
      expect(saveButton).toBeInTheDocument();
      expect(saveButton).toBeDisabled();
      expect(screen.queryByText(UNSAVED_HINT)).not.toBeInTheDocument();
    });
  });

  describe('Saving changes', () => {
    it('calls saveFieldset on save button click with changes', () => {
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ id: 10, title: 'Old Title' }) }));

      act(() => {
        getFieldsetSettingsProps().onTitleChange({ target: { value: 'New Title' } });
      });

      expect(screen.getByRole('button', { name: SAVE_LABEL })).not.toBeDisabled();
      expect(screen.getByText(UNSAVED_HINT)).toBeInTheDocument();

      userEvent.click(screen.getByRole('button', { name: SAVE_LABEL }));

      expect(saveFieldset).toHaveBeenCalledTimes(1);
      expect(saveFieldset).toHaveBeenCalledWith(
        expect.objectContaining({
          fieldset: expect.objectContaining({ id: 10 }),
          isChanged: true,
          fieldsetChanges: expect.objectContaining({ title: 'New Title' }),
        }),
      );
    });
  });

  describe('Reverting unsaved changes', () => {
    it('disables Save button and hides unsaved hint when Label Position is reverted', () => {
      render(
        React.createElement(FieldsetDetailsForm, {
          fieldset: makeFieldset({ id: 10, labelPosition: EFieldLabelPosition.Top }),
        }),
      );

      act(() => {
        getFieldsetSettingsProps().onLabelPositionChange(EFieldLabelPosition.Left);
      });

      expect(screen.getByRole('button', { name: SAVE_LABEL })).not.toBeDisabled();
      expect(screen.getByText(UNSAVED_HINT)).toBeInTheDocument();

      act(() => {
        getFieldsetSettingsProps().onLabelPositionChange(EFieldLabelPosition.Top);
      });

      expect(screen.getByRole('button', { name: SAVE_LABEL })).toBeDisabled();
      expect(screen.queryByText(UNSAVED_HINT)).not.toBeInTheDocument();
    });

    it('disables Save button and hides unsaved hint when title is reverted', () => {
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ id: 10, title: 'Original Title' }) }));

      act(() => {
        getFieldsetSettingsProps().onTitleChange({ target: { value: 'Original Title!' } });
      });

      expect(screen.getByRole('button', { name: SAVE_LABEL })).not.toBeDisabled();
      expect(screen.getByText(UNSAVED_HINT)).toBeInTheDocument();

      act(() => {
        getFieldsetSettingsProps().onTitleChange({ target: { value: 'Original Title' } });
      });

      expect(screen.getByRole('button', { name: SAVE_LABEL })).toBeDisabled();
      expect(screen.queryByText(UNSAVED_HINT)).not.toBeInTheDocument();
    });
  });

  describe('External rules sync', () => {
    it('re-syncs fieldset rules from props and keeps Save disabled on external fieldset update', () => {
      const initialFieldset = makeFieldset({
        id: 10,
        rulesets: [makeFieldsetRuleset({ apiName: 'rule-1' })],
      });
      const { rerender } = render(React.createElement(FieldsetDetailsForm, { fieldset: initialFieldset }));

      const updatedFieldset = makeFieldset({
        id: 10,
        rulesets: [makeFieldsetRuleset({ apiName: 'rule-2' })],
      });
      rerender(React.createElement(FieldsetDetailsForm, { fieldset: updatedFieldset }));

      expect(screen.getByRole('button', { name: SAVE_LABEL })).toBeDisabled();
    });
  });

  describe('Readonly mode when fieldset is linked to templates', () => {
    const LINKED_USAGE = [{ id: 1, name: 'Template 1' }];

    it('passes isReadOnly=true to child components when usage is present', () => {
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ usage: LINKED_USAGE }) }));

      expect(getModifyDropdownProps().isReadOnly).toBe(true);
      expect(getFieldsetSettingsProps().isReadOnly).toBe(true);
      expect(getFieldsetFieldsListProps().isReadOnly).toBe(true);
      expect(getFieldsetRulesetsListProps().isReadOnly).toBe(true);
    });

    it('hides Save bar when isLinked', () => {
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ usage: LINKED_USAGE }) }));
      expect(screen.queryByRole('button', { name: SAVE_LABEL })).not.toBeInTheDocument();
    });
  });

  describe('Field rule modal integration', () => {
    it('opens FieldRuleModal when onOpenFieldRule callback is called', () => {
      const fields = [makeFieldsetField({ apiName: 'f1', order: 1, type: EExtraFieldType.String })];
      render(React.createElement(FieldsetDetailsForm, { fieldset: makeFieldset({ fields }) }));

      expect(screen.queryByTestId('field-rule-modal')).not.toBeInTheDocument();

      const { onOpenFieldRule } = getFieldsetFieldsListProps();
      act(() => {
        onOpenFieldRule('f1');
      });

      expect(screen.getByTestId('field-rule-modal')).toBeInTheDocument();
    });
  });
});
