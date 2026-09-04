import * as React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch } from 'react-redux';

import { FieldsetCard } from '../FieldsetCard';
import { ModifyDropdown } from '../../../UI';

import {
  openEditModal,
  deleteFieldsetAction,
  cloneFieldsetAction,
  setCurrentFieldset,
} from '../../../../redux/fieldsets/slice';
import { history } from '../../../../utils/history';
import { intlMock } from '../../../../__stubs__/intlMock';
import { IFieldsetField } from '../../../../types/fieldset';
import { makeFieldsetCatalogItem, makeFieldsetTemplateRule } from '../../../../__stubs__/fieldsets.factory';

jest.mock('../../../../utils/history', () => ({
  history: { push: jest.fn(), location: { pathname: '/' }, listen: jest.fn() },
}));

jest.mock('../../../../utils/strings', () => ({
  sanitizeText: jest.fn((text: string) => text),
}));

jest.mock('../../../../redux/fieldsets/slice', () => ({
  openEditModal: jest.fn(() => ({ type: 'fieldsets/openEditModal' })),
  deleteFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/deleteFieldsetAction', payload: p })),
  cloneFieldsetAction: jest.fn((p) => ({ type: 'fieldsets/cloneFieldsetAction', payload: p })),
  setCurrentFieldset: jest.fn((p) => ({ type: 'fieldsets/setCurrentFieldset', payload: p })),
}));

jest.mock('../../../UI', () => ({
  ModifyDropdown: jest.fn(() => null),
}));

jest.mock('../../../icons', () => ({
  MoreIcon: () => null,
  PencilIcon: () => null,
  TrashIcon: () => null,
  UnionIcon: () => null,
}));

describe('FieldsetCard', () => {
  const mockDispatch = jest.fn();

  const formatMsg = (id: string, values?: Record<string, string | number>): string =>
    intlMock.formatMessage({ id }, values) as string;
  const FIELDS_STATS = (count: number) => formatMsg('fieldsets.stats.fields', { count });
  const RULES_STATS = (count: number) => formatMsg('fieldsets.stats.rules', { count });

  let fieldCounter = 0;

  const makeField = (overrides: Partial<IFieldsetField> = {}): IFieldsetField => ({
    type: 'string',
    name: 'Field',
    order: 0,
    apiName: `f-${++fieldCounter}`,
    ...overrides,
  });

  const makeProps = makeFieldsetCatalogItem;

  const getModifyDropdownProps = () => {
    const mock = ModifyDropdown as jest.Mock;
    const lastCall = mock.mock.calls[mock.mock.calls.length - 1];
    return lastCall[0];
  };

  beforeEach(() => {
    jest.clearAllMocks();
    fieldCounter = 0;
    (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  });

  describe('Navigation', () => {
    it('navigates to detail page on title click', () => {
      render(React.createElement(FieldsetCard, makeProps({ id: 10 })));

      const titleLink = screen.getByRole('link');
      userEvent.click(titleLink);

      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith('/fieldsets/10/');
    });

    it('navigates to detail page on Enter key', () => {
      render(React.createElement(FieldsetCard, makeProps({ id: 10 })));

      const titleLink = screen.getByRole('link');
      titleLink.focus();
      userEvent.keyboard('{Enter}');

      expect(history.push).toHaveBeenCalledTimes(1);
      expect(history.push).toHaveBeenCalledWith('/fieldsets/10/');
    });
  });

  describe('Dropdown — Edit', () => {
    it('dispatches setCurrentFieldset and openEditModal on Edit click', () => {
      const props = makeProps();
      render(React.createElement(FieldsetCard, props));

      act(() => {
        getModifyDropdownProps().onEdit();
      });

      expect(mockDispatch).toHaveBeenCalledWith(
        setCurrentFieldset({
          id: props.id,
          apiName: props.apiName,
          name: props.name,
          description: props.description,
          labelPosition: props.labelPosition,
          layout: props.layout,
          order: props.order,
          title: props.title,
          rules: props.rules,
          fields: props.fields,
          usage: props.usage,
        }),
      );
      expect(mockDispatch).toHaveBeenCalledWith(openEditModal());
      expect(mockDispatch).toHaveBeenCalledTimes(2);
    });
  });

  describe('Dropdown — Delete', () => {
    it('dispatches deleteFieldsetAction on Delete click', () => {
      render(React.createElement(FieldsetCard, makeProps({ id: 10 })));

      act(() => {
        getModifyDropdownProps().onDelete();
      });

      expect(mockDispatch).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(deleteFieldsetAction({ id: 10 }));
    });
  });

  describe('Dropdown — Clone', () => {
    it('dispatches cloneFieldsetAction on Clone click', () => {
      const props = makeProps({ id: 10 });
      render(React.createElement(FieldsetCard, props));

      act(() => {
        getModifyDropdownProps().onClone();
      });

      expect(mockDispatch).toHaveBeenCalledTimes(1);
      expect(mockDispatch).toHaveBeenCalledWith(cloneFieldsetAction({ id: 10 }));
    });
  });

  describe('ModifyDropdown — isReadOnly state (linked fieldsets)', () => {
    it('passes isReadOnly=true to ModifyDropdown when usage contains linked templates', () => {
      const props = makeProps({
        usage: [{ id: 1, name: 'Template 1' }],
      });
      render(React.createElement(FieldsetCard, props));

      expect(getModifyDropdownProps().isReadOnly).toBe(true);
    });

    it('passes isReadOnly=false to ModifyDropdown when usage is empty', () => {
      const props = makeProps({ usage: [] });
      render(React.createElement(FieldsetCard, props));

      expect(getModifyDropdownProps().isReadOnly).toBe(false);
    });
  });

  describe('Statistics footer', () => {
    it('shows field count and rule count when both are > 0', () => {
      const props = makeProps({
        fields: [makeField(), makeField()],
        rules: [makeFieldsetTemplateRule()],
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
      render(React.createElement(FieldsetCard, makeProps({ fields: [], rules: [makeFieldsetTemplateRule()] })));

      expect(screen.getByText(RULES_STATS(1))).toBeInTheDocument();
      expect(screen.queryByText(FIELDS_STATS(0))).not.toBeInTheDocument();
    });
  });
});
