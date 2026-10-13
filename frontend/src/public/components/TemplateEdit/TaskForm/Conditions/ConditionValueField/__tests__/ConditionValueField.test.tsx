/// <reference types="jest" />
import * as React from 'react';
import { render, screen } from '@testing-library/react';
import { IntlProvider } from 'react-intl';

import { enMessages } from '../../../../../../lang/locales/en_US';
import { EExtraFieldType } from '../../../../../../types/template';
import { TTaskVariable } from '../../../../types';
import { EConditionLogicOperations, EConditionOperators, TConditionRule } from '../../types';
import { ConditionValueField } from '../ConditionValueField';

jest.mock('react-redux', () => {
  const actual = jest.requireActual('react-redux');

  return {
    ...actual,
    useSelector: jest.fn((selector: (state: { groups: { list: unknown[] } }) => unknown) =>
      selector({ groups: { list: [] } }),
    ),
    useDispatch: () => jest.fn(),
  };
});

jest.mock('../../../../../Field', () => ({
  Field: () => null,
}));

jest.mock('../../utils/useLazyDataset', () => ({
  useLazyDataset: jest.fn(() => undefined),
}));

jest.mock('../../../../../UI/form/DatePicker', () => ({
  DatePickerCustom: ({ selected }: { selected: Date | null }) => (
    <span data-testid="condition-date-picker">{selected ? 'has-date' : 'empty'}</span>
  ),
}));

type TConditionEntity = {
  id: number;
  entityType: 'user' | 'group';
  value: string;
};

const buildDropdownEntities = (): TConditionEntity[] => {
  const labelUsers: TConditionEntity[] = [{ id: 5, entityType: 'user', value: 'user-5' }];
  const labelGroups: TConditionEntity[] = [{ id: 5, entityType: 'group', value: 'group-5' }];

  return [...labelGroups, ...labelUsers];
};

const findSelectedEntity = (entities: TConditionEntity[], rule: { value: number; fieldType: 'user' | 'group' }) =>
  entities.find((entity) => entity.id === Number(rule.value) && entity.entityType === rule.fieldType) || null;

const dateVariable: TTaskVariable = {
  title: 'Deadline',
  apiName: 'date-deadline',
  type: EExtraFieldType.Date,
};

const makeDateRule = (overrides: Partial<TConditionRule> = {}): TConditionRule =>
  ({
    ruleApiName: 'rule-1',
    predicateApiName: 'pred-1',
    logicOperation: EConditionLogicOperations.And,
    field: dateVariable.apiName,
    fieldType: EExtraFieldType.Date,
    operator: null,
    value: undefined,
    ...overrides,
  }) as TConditionRule;

const renderValueField = (props: Partial<React.ComponentProps<typeof ConditionValueField>> = {}) =>
  render(
    <IntlProvider locale="en" messages={enMessages}>
      <ConditionValueField
        variable={dateVariable}
        operator={null}
        rule={makeDateRule()}
        users={[]}
        isDisabled={false}
        changeRuleValue={jest.fn()}
        {...props}
      />
    </IntlProvider>,
  );

describe('ConditionValueField user/group selection logic', () => {
  const dropdownEntities = buildDropdownEntities();

  it('selects user entity by id and fieldType when user and group share the same id', () => {
    const selectedEntity = findSelectedEntity(dropdownEntities, { value: 5, fieldType: 'user' });

    expect(selectedEntity).toMatchObject({ id: 5, entityType: 'user' });
  });

  it('selects group entity by id and fieldType when user and group share the same id', () => {
    const selectedEntity = findSelectedEntity(dropdownEntities, { value: 5, fieldType: 'group' });

    expect(selectedEntity).toMatchObject({ id: 5, entityType: 'group' });
  });

  it('does not mark group as selected when only user is chosen', () => {
    const rule = { value: 5, fieldType: 'user' as const };
    const groupEntity = dropdownEntities.find((entity) => entity.entityType === 'group');

    expect(groupEntity?.id === rule.value && groupEntity?.entityType === rule.fieldType).toBe(false);
  });
});

describe('ConditionValueField date field', () => {
  it('does not crash when a date field is selected before an operator', () => {
    expect(() => renderValueField()).not.toThrow();
    expect(screen.queryByTestId('condition-date-picker')).not.toBeInTheDocument();
  });

  it('shows the date picker after choosing an operator with a value', () => {
    const { rerender } = renderValueField();

    rerender(
      <IntlProvider locale="en" messages={enMessages}>
        <ConditionValueField
          variable={dateVariable}
          operator={EConditionOperators.Equal}
          rule={makeDateRule({ operator: EConditionOperators.Equal })}
          users={[]}
          isDisabled={false}
          changeRuleValue={jest.fn()}
        />
      </IntlProvider>,
    );

    expect(screen.getByTestId('condition-date-picker')).toHaveTextContent('empty');
  });

  it('does not crash when switching from equals to exists', () => {
    const { rerender } = renderValueField({
      operator: EConditionOperators.Equal,
      rule: makeDateRule({ operator: EConditionOperators.Equal, value: 1718409600 }),
    });

    expect(screen.getByTestId('condition-date-picker')).toHaveTextContent('has-date');

    expect(() =>
      rerender(
        <IntlProvider locale="en" messages={enMessages}>
          <ConditionValueField
            variable={dateVariable}
            operator={EConditionOperators.Exist}
            rule={makeDateRule({ operator: EConditionOperators.Exist })}
            users={[]}
            isDisabled={false}
            changeRuleValue={jest.fn()}
          />
        </IntlProvider>,
      ),
    ).not.toThrow();

    expect(screen.queryByTestId('condition-date-picker')).not.toBeInTheDocument();
  });
});
