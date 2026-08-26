import { EConditionAction, EConditionLogicOperations, EConditionOperators, ICondition } from '../../../TaskForm/Conditions';
import { countCheckIfConditions, isCheckIfCondition } from '../countCheckIfConditions';

function createCondition(action: EConditionAction, field = 'field-1'): ICondition {
  return {
    apiName: `condition-${action}`,
    order: 1,
    action,
    rules: [
      {
        ruleApiName: 'rule-1',
        predicateApiName: 'predicate-1',
        field,
        operator: EConditionOperators.Exist,
        logicOperation: EConditionLogicOperations.And,
      },
    ],
  };
}

describe('countCheckIfConditions', () => {
  it('should ignore start-after conditions', () => {
    expect(countCheckIfConditions([createCondition(EConditionAction.StartTask)])).toBe(0);
  });

  it('should count filled skip-task and end-process rules', () => {
    const conditions = [
      createCondition(EConditionAction.StartTask),
      createCondition(EConditionAction.SkipTask),
      createCondition(EConditionAction.EndProcess),
    ];

    expect(countCheckIfConditions(conditions)).toBe(2);
  });

  it('should skip empty check-if placeholders', () => {
    expect(countCheckIfConditions([
      {
        ...createCondition(EConditionAction.SkipTask),
        rules: [{
          ruleApiName: 'empty',
          predicateApiName: 'empty',
          field: null,
          operator: null,
          logicOperation: EConditionLogicOperations.And,
        }],
      },
    ])).toBe(0);
  });

  it('should treat missing conditions as zero', () => {
    expect(countCheckIfConditions(undefined)).toBe(0);
  });
});

describe('isCheckIfCondition', () => {
  it('should accept skip-task and end-process only', () => {
    expect(isCheckIfCondition(createCondition(EConditionAction.SkipTask))).toBe(true);
    expect(isCheckIfCondition(createCondition(EConditionAction.EndProcess))).toBe(true);
    expect(isCheckIfCondition(createCondition(EConditionAction.StartTask))).toBe(false);
  });
});
