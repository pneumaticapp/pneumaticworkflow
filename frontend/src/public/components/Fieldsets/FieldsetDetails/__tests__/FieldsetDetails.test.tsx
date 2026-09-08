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
} from '../../../../redux/fieldsets/slice';
import { ModifyDropdown } from '../../../UI';
import { IExtraField, EExtraFieldType } from '../../../../types/template';
import { makeFieldsetCatalogItem, makeFieldsetRuleset } from '../../../../__stubs__/fieldsets.factory';
import { makeExtraField } from '../../../../__stubs__/fields.factory';
import { FieldsetSettings } from '../FieldsetSettings/FieldsetSettings';
import { FieldsetFieldsList } from '../FieldsetFieldsList/FieldsetFieldsList';
import { FieldsetRulesetsList } from '../FieldsetRulesetsList/FieldsetRulesetsList';
import { IApplicationState } from '../../../../types/redux';
import { saveFieldset, cloneFieldset } from '../utils';

jest.mock('../utils', () => ({
  ...jest.requireActual('../utils'),
  saveFieldset: jest.fn(),
  cloneFieldset: jest.fn(),
}));

jest.mock('../../../../utils/history', () => ({
  history: {
    push: jest.fn(),
    location: { pathname: '/' },
    listen: jest.fn(),
    length: 1,
    action: 'PUSH',
    go: jest.fn(),
    goBack: jest.fn(),
    goForward: jest.fn(),
    replace: jest.fn(),
    block: jest.fn(),
    createHref: jest.fn(),
  },
}));

jest.mock('../../../../redux/fieldsets/slice', () => ({
  openEditModal: jest.fn(() => ({ type: 'fieldsets/openEditModal' })),
  deleteFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/deleteFieldsetAction', payload: p })),
  cloneFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/cloneFieldsetAction', payload: p })),
  loadCurrentFieldset: jest.fn((p) => ({ type: 'fieldsets/loadCurrentFieldset', payload: p })),
  resetCurrentFieldset: jest.fn(() => ({ type: 'fieldsets/resetCurrentFieldset' })),
  updateFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/updateFieldsetAction', payload: p })),
}));

jest.mock('../../../UI', () => ({
  ModifyDropdown: jest.fn((props: { onClone?: () => void }) =>
    React.createElement('div', null, React.createElement('button', { 'data-testid': 'modify-clone', onClick: props.onClone })),
  ),
  Button: jest.fn((props: { label: string; onClick?: () => void; disabled?: boolean }) =>
    React.createElement('button', { onClick: props.onClick, disabled: props.disabled }, props.label),
  ),
  RouteLeavingGuard: jest.fn(() => null),
}));

jest.mock('../../FieldsetModal/FieldsetModal', () => ({
  FieldsetModal: jest.fn(() => null),
}));

jest.mock('../FieldsetDetailsSkeleton', () => ({
  FieldsetDetailsSkeleton: jest.fn(() => React.createElement('div', { role: 'status', 'aria-label': 'Loading' })),
}));

jest.mock('../FieldRuleModal', () => ({
  FieldRuleModal: jest.fn((props: { isOpen: boolean }) =>
    props.isOpen ? React.createElement('div', { 'data-testid': 'field-rule-modal' }) : null,
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

describe('FieldsetDetails', () => {
  const mockDispatch = jest.fn();
  const formatMsg = (id: string) => intlMock.formatMessage({ id });

  const SAVE_LABEL = formatMsg('fieldsets.save');
  const UNSAVED_HINT = formatMsg('fieldsets.unsaved-changes');

  const makeProps = (id: string = '10'): TFieldsetDetailsProps => ({
    match: { params: { id }, isExact: true, path: '', url: '' },
    location: { pathname: `/fieldsets/${id}/`, search: '', hash: '', state: undefined },
    history,
  });

  const makeField = (overrides: Partial<IExtraField> = {}) => makeExtraField(overrides);

  const loadingState: Partial<IApplicationState> = {
    fieldsets: { currentFieldset: null, isCurrentFieldsetLoading: true } as IApplicationState['fieldsets'],
    authUser: { account: { id: 1 } } as IApplicationState['authUser'],
    accounts: { users: [] } as unknown as IApplicationState['accounts'],
  };

  const nullFieldsetState: Partial<IApplicationState> = {
    fieldsets: { currentFieldset: null, isCurrentFieldsetLoading: false } as IApplicationState['fieldsets'],
    authUser: { account: { id: 1 } } as IApplicationState['authUser'],
    accounts: { users: [] } as unknown as IApplicationState['accounts'],
  };

  const makeLoadedState = (fieldsetOverrides = {}): Partial<IApplicationState> => {
    const fieldset = makeFieldsetCatalogItem({
      id: 10,
      layout: 'horizontal' as const,
      ...fieldsetOverrides,
    });
    return {
      fieldsets: { currentFieldset: fieldset, isCurrentFieldsetLoading: false } as IApplicationState['fieldsets'],
      authUser: { account: { id: 1 } } as IApplicationState['authUser'],
      accounts: { users: [] } as unknown as IApplicationState['accounts'],
    };
  };

  const getModifyDropdownProps = () => (ModifyDropdown as unknown as jest.Mock).mock.calls[0][0];
  const getFieldsetSettingsProps = () => {
    const calls = (FieldsetSettings as unknown as jest.Mock).mock.calls;
    return calls[calls.length - 1][0];
  };
  const getFieldsetFieldsListProps = () => {
    const calls = (FieldsetFieldsList as unknown as jest.Mock).mock.calls;
    return calls[calls.length - 1][0];
  };
  const getFieldsetRulesetsListProps = () => {
    const calls = (FieldsetRulesetsList as unknown as jest.Mock).mock.calls;
    return calls[calls.length - 1][0];
  };

  const mockSelectorState = (state: Partial<IApplicationState>) => {
    (useSelector as unknown as jest.Mock).mockImplementation(
      (selector: (state: IApplicationState) => unknown) => selector(state as IApplicationState),
    );
  };

  const renderWithState = (state: Partial<IApplicationState>, props = makeProps()) => {
    mockSelectorState(state);
    return render(React.createElement(FieldsetDetails, props));
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as unknown as jest.Mock).mockReturnValue(mockDispatch);
    mockSelectorState(loadingState);
  });

  describe('URL parameter validation', () => {
    it('redirects to fieldsets list on invalid id', () => {
      render(React.createElement(FieldsetDetails, makeProps('xyz')));
      const expectedRoute = ERoutes.Fieldsets;
      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith(expectedRoute);
    });

    it('dispatches loadCurrentFieldset on valid params', () => {
      render(React.createElement(FieldsetDetails, makeProps('10')));
      expect(history.push).not.toHaveBeenCalled();
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
      props.onEdit();
      expect(openEditModal).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(openEditModal());
    });

    it('onDelete in ModifyDropdown dispatches deleteFieldsetAction with onSuccess callback', () => {
      renderWithState(makeLoadedState({ id: 10 }), makeProps('10'));
      const props = getModifyDropdownProps();
      props.onDelete();
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
      renderWithState(makeLoadedState({ id: 10 }), makeProps('10'));
      const props = getModifyDropdownProps();

      expect(props.cloneLabel).toBe(formatMsg('fieldsets.clone'));

      props.onClone();
      expect(cloneFieldset).toHaveBeenCalledTimes(1);
      expect(cloneFieldset).toHaveBeenCalledWith(
        expect.objectContaining({ fieldsetId: 10 }),
      );
    });

    it('skips loadCurrentFieldset when fieldset is already loaded with same id', () => {
      renderWithState(makeLoadedState({ id: 10 }), makeProps('10'));
      expect(loadCurrentFieldset).not.toHaveBeenCalled();
    });
  });

  describe('Initial save bar state', () => {
    it('shows disabled Save button on initial render', () => {
      const fields = [makeField({ apiName: 'f1', order: 1 })];
      const rulesets = [makeFieldsetRuleset({ apiName: 'rule-1', fields: ['f1'] })];
      renderWithState(makeLoadedState({ fields, rulesets }));

      const saveButton = screen.getByRole('button', { name: SAVE_LABEL });
      expect(saveButton).toBeInTheDocument();
      expect(saveButton).toBeDisabled();
      expect(screen.queryByText(UNSAVED_HINT)).not.toBeInTheDocument();
    });
  });

  describe('Saving changes', () => {
    it('calls saveFieldset on save button click with changes', () => {
      renderWithState(makeLoadedState({ id: 10, title: 'Old Title' }));

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

  describe('External rules sync', () => {
    it('re-syncs detailFieldset rules from store and hides save bar on external fieldset update', () => {
      const initialState = makeLoadedState({
        id: 10,
        rulesets: [makeFieldsetRuleset({ apiName: 'rule-1' })],
      });
      mockSelectorState(initialState);
      const { rerender } = render(React.createElement(FieldsetDetails, makeProps()));

      const updatedState = makeLoadedState({
        id: 10,
        rulesets: [makeFieldsetRuleset({ apiName: 'rule-2' })],
      });
      mockSelectorState(updatedState);
      rerender(React.createElement(FieldsetDetails, makeProps()));

      expect(screen.getByRole('button', { name: SAVE_LABEL })).toBeDisabled();
    });
  });

  describe('Readonly mode when fieldset is linked to templates', () => {
    const LINKED_USAGE = [{ id: 1, name: 'Template 1' }];

    it('passes isReadOnly=true to child components when usage is present', () => {
      renderWithState(makeLoadedState({ usage: LINKED_USAGE }));

      expect(getModifyDropdownProps().isReadOnly).toBe(true);
      expect(getFieldsetSettingsProps().isReadOnly).toBe(true);
      expect(getFieldsetFieldsListProps().isReadOnly).toBe(true);
      expect(getFieldsetRulesetsListProps().isReadOnly).toBe(true);
    });

    it('hides Save bar when isLinked', () => {
      renderWithState(makeLoadedState({ usage: LINKED_USAGE }));
      expect(screen.queryByRole('button', { name: SAVE_LABEL })).not.toBeInTheDocument();
    });
  });

  describe('Field rule modal integration', () => {
    it('opens FieldRuleModal when onOpenFieldRule callback is called', () => {
      const fields = [makeField({ apiName: 'f1', order: 1, type: EExtraFieldType.String })];
      renderWithState(makeLoadedState({ fields }));

      expect(screen.queryByTestId('field-rule-modal')).not.toBeInTheDocument();

      const { onOpenFieldRule } = getFieldsetFieldsListProps();
      act(() => {
        onOpenFieldRule('f1');
      });

      expect(screen.getByTestId('field-rule-modal')).toBeInTheDocument();
    });
  });
});
