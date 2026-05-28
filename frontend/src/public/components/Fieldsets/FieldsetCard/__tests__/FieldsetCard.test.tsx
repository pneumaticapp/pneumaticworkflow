import * as React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { FieldsetCard } from '../FieldsetCard';
import { Dropdown } from '../../../UI';
import { WarningPopup } from '../../../UI/WarningPopup';
import {
  openEditModal,
  deleteFieldsetAction,
  setCurrentFieldset,
} from '../../../../redux/fieldsets/slice';
import { history } from '../../../../utils/history';
import { intlMock } from '../../../../__stubs__/intlMock';
import { IFieldsetCardProps } from '../types';
import { IFieldsetField, IFieldsetTemplateRule } from '../../../../types/fieldset';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../../utils/strings', () => ({
  sanitizeText: jest.fn((text: string) => text),
}));

jest.mock('../../../../redux/fieldsets/slice', () => ({
  openEditModal: jest.fn(() => ({ type: 'fieldsets/openEditModal' })),
  deleteFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/deleteFieldsetAction', payload: p })),
  setCurrentFieldset: jest.fn((p) => ({ type: 'fieldsets/setCurrentFieldset', payload: p })),
}));

jest.mock('../../../UI', () => ({
  Dropdown: jest.fn(() => null),
}));

jest.mock('../../../UI/WarningPopup', () => ({
  WarningPopup: jest.fn(() => null),
}));

jest.mock('../../../icons', () => ({
  MoreIcon: () => null,
  PencilIcon: () => null,
  TrashIcon: () => null,
}));

describe('FieldsetCard', () => {
  const mockDispatch = jest.fn();

  const formatMsg = (id: string) => intlMock.formatMessage({ id });
  const EDIT_LABEL = formatMsg('fieldsets.edit');
  const DELETE_LABEL = formatMsg('fieldsets.delete');
  const FIELDS_STATS = (count: number) => intlMock.formatMessage({ id: 'fieldsets.stats.fields' }, { count });
  const RULES_STATS = (count: number) => intlMock.formatMessage({ id: 'fieldsets.stats.rules' }, { count });

  let fieldCounter = 0;
  let ruleCounter = 0;

  const makeField = (overrides: Partial<IFieldsetField> = {}): IFieldsetField => ({
    type: 'string',
    name: 'Field',
    order: 0,
    api_name: `f-${++fieldCounter}`,
    ...overrides,
  });

  const makeRule = (overrides: Partial<IFieldsetTemplateRule> = {}): IFieldsetTemplateRule => ({
    id: ++ruleCounter,
    type: 'sum_equal',
    value: '100',
    fields: [],
    ...overrides,
  });

  const makeProps = (overrides: Partial<IFieldsetCardProps> = {}): IFieldsetCardProps => ({
    id: 10,
    apiName: 'fs-10',
    name: 'Test Fieldset',
    description: 'A test fieldset',
    labelPosition: 'top',
    layout: 'vertical',
    order: 0,
    kickoffId: null,
    taskId: null,
    rules: [],
    fields: [],
    templateId: 5,
    ...overrides,
  });

  const getDropdownOptions = () => {
    const mock = Dropdown as unknown as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0].options;
  };

  const findDropdownOption = (label: string) => {
    return getDropdownOptions().find((opt: { label: string }) => opt.label === label);
  };

  const getWarningPopupProps = () => {
    const mock = WarningPopup as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0];
  };

  beforeEach(() => {
    jest.clearAllMocks();
    fieldCounter = 0;
    ruleCounter = 0;
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  describe('Navigation', () => {
    it('navigates to detail page on title click', () => {
      render(React.createElement(FieldsetCard, makeProps({ id: 10, templateId: 5 })));

      const titleLink = screen.getByRole('link');
      userEvent.click(titleLink);

      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith('/templates/5/fieldsets/10/');
    });

    it('navigates to detail page on Enter key', () => {
      render(React.createElement(FieldsetCard, makeProps({ id: 10, templateId: 5 })));

      const titleLink = screen.getByRole('link');
      titleLink.focus();
      userEvent.keyboard('{Enter}');

      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith('/templates/5/fieldsets/10/');
    });
  });

  describe('Dropdown — Edit', () => {
    it('dispatches setCurrentFieldset and openEditModal on Edit click', () => {
      const props = makeProps();
      render(React.createElement(FieldsetCard, props));

      const editOption = findDropdownOption(EDIT_LABEL);
      editOption.onClick();

      expect(mockDispatch).toHaveBeenCalledWith(
        setCurrentFieldset({
          id: props.id,
          templateId: props.templateId,
          name: props.name,
          description: props.description,
          labelPosition: props.labelPosition,
          layout: props.layout,
          order: props.order,
          kickoffId: props.kickoffId,
          taskId: props.taskId,
          rules: props.rules,
          fields: props.fields,
        }),
      );
      expect(mockDispatch).toHaveBeenCalledWith(openEditModal());
      expect(mockDispatch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Dropdown — Delete', () => {
    it('opens WarningPopup on Delete click', () => {
      render(React.createElement(FieldsetCard, makeProps()));

      expect(getWarningPopupProps().isOpen).toBe(false);

      const deleteOption = findDropdownOption(DELETE_LABEL);
      act(() => { deleteOption.onClick(); });

      expect(getWarningPopupProps().isOpen).toBe(true);
    });

    it('dispatches deleteFieldsetAction on WarningPopup confirm', () => {
      render(React.createElement(FieldsetCard, makeProps({ id: 10 })));

      act(() => { findDropdownOption(DELETE_LABEL).onClick(); });
      act(() => { getWarningPopupProps().onConfirm(); });

      expect(mockDispatch).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(deleteFieldsetAction({ id: 10 }));

      expect(getWarningPopupProps().isOpen).toBe(false);
    });

    it('closes WarningPopup without dispatch on cancel', () => {
      render(React.createElement(FieldsetCard, makeProps()));

      act(() => { findDropdownOption(DELETE_LABEL).onClick(); });
      expect(getWarningPopupProps().isOpen).toBe(true);

      act(() => { getWarningPopupProps().onReject(); });

      expect(getWarningPopupProps().isOpen).toBe(false);
      expect(deleteFieldsetAction).not.toHaveBeenCalled();
    });
  });

  describe('Statistics footer', () => {
    it('shows field count and rule count when both are > 0', () => {
      const props = makeProps({
        fields: [makeField(), makeField()],
        rules: [makeRule()],
      });
      render(React.createElement(FieldsetCard, props));

      expect(screen.getByText(FIELDS_STATS(2))).toBeInTheDocument();
      expect(screen.getByText(RULES_STATS(1))).toBeInTheDocument();
    });

    it('hides footer when fields and rules are both empty', () => {
      render(React.createElement(FieldsetCard, makeProps({ fields: [], rules: [] })));

      expect(screen.queryByText(FIELDS_STATS(0))).not.toBeInTheDocument();
      expect(screen.queryByText(RULES_STATS(0))).not.toBeInTheDocument();
    });

    it('shows only fields count when rules are empty', () => {
      render(React.createElement(FieldsetCard, makeProps({ fields: [makeField()], rules: [] })));

      expect(screen.getByText(FIELDS_STATS(1))).toBeInTheDocument();
      expect(screen.queryByText(RULES_STATS(0))).not.toBeInTheDocument();
    });

    it('shows only rules count when fields are empty', () => {
      render(React.createElement(FieldsetCard, makeProps({ fields: [], rules: [makeRule()] })));

      expect(screen.getByText(RULES_STATS(1))).toBeInTheDocument();
      expect(screen.queryByText(FIELDS_STATS(0))).not.toBeInTheDocument();
    });
  });
});
