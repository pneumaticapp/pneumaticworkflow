import { EExtraFieldType, ITemplateTask } from '../../../../types/template';
import { createEmptyDueDate } from '../../../../utils/dueDate/createEmptyDueDate';
import { omit } from '../../../../utils/helpers';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../TaskForm/Conditions';
import { getClonedTask } from '../getClonedTask';

describe('getClonedTask', () => {
  it('returns initial task\'s copy', () => {
    const mockTask: ITemplateTask = {
      id: 3048,
      apiName: 'task-1',
      name: 'Task 1',
      description: 'Check data on correct. If it\'s not - requesting for actualisation to user.',
      number: 1,
      requireCompletionByAll: true,
      fields: [
        {
          name: 'Large Text Field',
          type: EExtraFieldType.Text,
          isRequired: false,
          description: '',
          apiName: 'large-text-field-8622',
          selections: [],
          order: 0,
        },
      ],
      rawPerformers: [],
      delay: null,
      rawDueDate: createEmptyDueDate(),
      conditions: [
        {
          apiName: 'condition-40a910',
          order: 1,
          action: EConditionAction.EndProcess,
          rules: [
            {
              ruleId: 12,
              ruleApiName: 'rule-2fw333',
              predicateId: 318,
              predicateApiName: 'predicate-wqef3r',
              field: 'client-name-kickoff',
              operator: EConditionOperators.Contain,
              fieldType: EExtraFieldType.Text,
              logicOperation: EConditionLogicOperations.And,
            },
            {
              ruleId: 12,
              ruleApiName: 'rule-2fw333',
              predicateId: 319,
              predicateApiName: 'predicate-wqewed',
              field: 'client-name-kickoff',
              operator: EConditionOperators.Contain,
              fieldType: EExtraFieldType.Text,
              logicOperation: EConditionLogicOperations.And,
            },
            {
              ruleId: 13,
              ruleApiName: 'rule-2fw444',
              predicateId: 320,
              predicateApiName: 'predicate-wdwede',
              field: 'client-name-kickoff',
              operator: EConditionOperators.Contain,
              fieldType: EExtraFieldType.Text,
              logicOperation: EConditionLogicOperations.Or,
            },
            {
              ruleId: 13,
              ruleApiName: 'rule-2fw444',
              predicateId: 321,
              predicateApiName: 'predicate-wdwe45',
              field: 'client-name-kickoff',
              operator: EConditionOperators.Contain,
              fieldType: EExtraFieldType.Text,
              logicOperation: EConditionLogicOperations.And,
            },
          ],
        },
      ],
      uuid: '5f6cbe6b-238e-462e-8f18-d5ee5ec45de3',
      checklists: [],
    };

    const clonedTask = getClonedTask(mockTask);

    const diffFields: (keyof ITemplateTask)[] = ['id', 'apiName', 'uuid', 'fields', 'conditions', 'delay', 'name', 'rawDueDate'];
    expect(omit(clonedTask, diffFields)).toStrictEqual(omit(mockTask, diffFields));
    expect(clonedTask.name).toBe(`${mockTask.name} (Clone)`);
    expect(clonedTask.id).toBe(undefined);
    expect(clonedTask.apiName).not.toBe(mockTask.apiName);
    expect(clonedTask.uuid).not.toBe(mockTask.uuid);
    expect(clonedTask.fields[0].id).toBe(undefined);
    expect(clonedTask.fields[0].apiName).not.toBe(mockTask.fields[0].apiName);
    expect(clonedTask.conditions[0].apiName).not.toBe(mockTask.conditions[0].apiName);
    expect(clonedTask.conditions[0].rules[0].ruleId).toBe(undefined);
    expect(clonedTask.conditions[0].rules[0].ruleApiName).toBe(clonedTask.conditions[0].rules[1].ruleApiName);
  });
});
