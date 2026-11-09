import * as React from 'react';
import * as ReactIntl from 'react-intl';
import { fireEvent, render, screen } from '@testing-library/react';

import { TaskRenderConditionsInfo } from '../TaskRenderConditionsInfo';
import { makeTemplateTaskClient } from '../../../../__stubs__/templates.factory';
import { arMessages } from '../../../../lang/locales/ar-SY';
import { EExtraFieldType } from '../../../../types/template';
import { EConditionAction, EConditionLogicOperations, EConditionOperators, ICondition } from '../../TaskForm/Conditions/types';

jest.mock('react-intl', () => ({ ...jest.requireActual('react-intl'), useIntl: jest.fn() }));
const mockUseIntl = ReactIntl.useIntl as jest.MockedFunction<typeof ReactIntl.useIntl>;

const condition = (action: EConditionAction, count: number): ICondition => ({
  action,
  apiName: 'condition-1',
  order: 0,
  rules: Array.from({ length: count }, (_, index) => ({
    ruleApiName: `rule-${index}`,
    predicateApiName: `predicate-${index}`,
    field: `field-${index}`,
    fieldType: EExtraFieldType.String,
    operator: EConditionOperators.Exist,
    logicOperation: EConditionLogicOperations.And,
  })),
});

describe('TaskRenderConditionsInfo Arabic counters', () => {
  beforeEach(() => {
    mockUseIntl.mockReturnValue(ReactIntl.createIntl({ locale: 'ar-SY', messages: arMessages }));
  });
  afterEach(() => jest.restoreAllMocks());

  it('renders the start-after dual while preserving click behavior and source conditions', () => {
    const onClick = jest.fn();
    const task = makeTemplateTaskClient({ conditions: [condition(EConditionAction.StartTask, 2)] });
    const source = JSON.stringify(task);
    render(<TaskRenderConditionsInfo task={task} onClick={onClick} isStartTask />);

    fireEvent.click(screen.getByRole('button', { name: 'شرطا بدء' }));
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(JSON.stringify(task)).toBe(source);
  });

  it('counts only filled check-if rules and formats their Arabic few form', () => {
    const filled = condition(EConditionAction.SkipTask, 3);
    const task = makeTemplateTaskClient({
      conditions: [
        condition(EConditionAction.StartTask, 2),
        { ...filled, rules: [...filled.rules, { ...filled.rules[0], field: null }] },
      ],
    });
    render(<TaskRenderConditionsInfo task={task} onClick={jest.fn()} />);

    expect(screen.getByRole('button')).toHaveTextContent(`${new Intl.NumberFormat('ar-SY').format(3)} شروط تحقق`);
  });
});
