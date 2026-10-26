import {
  createTemplateValidationError,
  getValidationErrorEntitySnapshot,
  getValidationErrorTarget,
} from '../getValidationErrorTarget';
import { initialTemplate } from '../../template/reducer';
import { makeExtraField } from '../../../__stubs__/fields.factory';
import {
  makeFieldsetBindingClient,
  makeFieldsetField,
  makeFieldsetTemplateRule,
} from '../../../__stubs__/fieldsets.factory';
import { makeKickoffClient, makeTemplateTaskClient } from '../../../__stubs__/templates.factory';
import { ETaskFormParts } from '../../../components/TemplateEdit/types';
import {
  EConditionAction,
  EConditionLogicOperations,
  ICondition,
} from '../../../components/TemplateEdit/TaskForm/Conditions/types';
import { EExtraFieldType, ETaskPerformerType, ITemplateClient } from '../../../types/template';

const makeCondition = (apiName: string, action: EConditionAction, predicateApiName: string): ICondition => ({
  apiName,
  order: 0,
  action,
  rules: [
    {
      ruleApiName: `${apiName}-rule`,
      predicateApiName,
      logicOperation: EConditionLogicOperations.And,
      field: 'field-1',
      operator: null,
    },
  ],
});

const task = makeTemplateTaskClient({
  apiName: 'task-1',
  uuid: 'task-uuid',
  rawPerformers: [{ apiName: 'performer-1', label: 'Ann', type: ETaskPerformerType.User, sourceId: '1' }],
  fields: [
    makeExtraField({
      apiName: 'task-field',
      type: EExtraFieldType.Radio,
      selections: [{ apiName: 'task-option', value: 'A' }],
    }),
  ],
  fieldsets: [
    makeFieldsetBindingClient({
      apiNameBinding: 'task-fieldset',
      fields: [makeFieldsetField({ apiName: 'fieldset-field' })],
    }),
  ],
  conditions: [
    makeCondition('condition-skip', EConditionAction.SkipTask, 'predicate-skip'),
    makeCondition('condition-start', EConditionAction.StartTask, 'predicate-start'),
  ],
  rawDueDate: { ...makeTemplateTaskClient().rawDueDate, apiName: 'due-date-1' },
  checklists: [{ apiName: 'clist-1', selections: [{ apiName: 'citem-1', value: 'Check' }] }],
});

const template: ITemplateClient = {
  ...initialTemplate.data,
  kickoff: makeKickoffClient({
    fields: [
      makeExtraField({
        apiName: 'kickoff-field',
        type: EExtraFieldType.Checkbox,
        selections: [{ apiName: 'kickoff-option', value: 'B' }],
      }),
    ],
    fieldsets: [
      makeFieldsetBindingClient({
        apiNameBinding: 'kickoff-fieldset',
        rules: [makeFieldsetTemplateRule({ apiName: 'kickoff-fieldset-rule' })],
      }),
    ],
  }),
  tasks: [task],
};

describe('getValidationErrorTarget', () => {
  it.each([
    ['kickoff-field', null, null, 'kickoff-field'],
    ['kickoff-option', null, null, 'kickoff-field'],
    ['kickoff-fieldset-rule', null, null, 'kickoff-fieldset'],
    ['task-1', 'task-uuid', null, 'task-1'],
    ['performer-1', 'task-uuid', ETaskFormParts.AssignPerformers, 'task-1'],
    ['task-option', 'task-uuid', ETaskFormParts.Fields, 'task-field'],
    ['fieldset-field', 'task-uuid', ETaskFormParts.Fields, 'task-fieldset'],
    ['condition-skip', 'task-uuid', ETaskFormParts.CheckIf, 'condition-skip'],
    ['condition-skip-rule', 'task-uuid', ETaskFormParts.CheckIf, 'condition-skip'],
    ['predicate-skip', 'task-uuid', ETaskFormParts.CheckIf, 'predicate-skip'],
    ['predicate-start', 'task-uuid', ETaskFormParts.StartsAfter, 'predicate-start'],
    ['due-date-1', 'task-uuid', ETaskFormParts.DueIn, 'due-date-1'],
    ['citem-1', 'task-uuid', null, 'citem-1'],
  ])('locates %s', (apiName, taskUuid, section, elementApiName) => {
    expect(getValidationErrorTarget(template, apiName)?.target).toEqual({ taskUuid, section, elementApiName });
  });

  it('returns null for an api_name that is not in the template', () => {
    expect(getValidationErrorTarget(template, 'unknown')).toBeNull();
  });

  it('builds the entity snapshot ignoring key order and server-derived keys', () => {
    expect(
      getValidationErrorEntitySnapshot({
        id: 1,
        apiName: 'a',
        order: 3,
        ancestors: ['x'],
        nested: [{ id: 2, value: 'b' }],
      }),
    ).toBe(getValidationErrorEntitySnapshot({ nested: [{ value: 'b' }], apiName: 'a', order: -1 }));
  });

  it('opens performers for a task error in the performers section and snapshots only performers', () => {
    const error = createTemplateValidationError(template, 'task-1', 'Add performers', ETaskFormParts.AssignPerformers);
    const changedDescription = { ...template, tasks: [{ ...task, description: 'Updated' }] };

    expect(error?.target).toEqual({
      taskUuid: 'task-uuid',
      section: ETaskFormParts.AssignPerformers,
      elementApiName: 'task-1',
    });
    expect(
      createTemplateValidationError(changedDescription, 'task-1', 'Add performers', ETaskFormParts.AssignPerformers)
        ?.entitySnapshot,
    ).toBe(error?.entitySnapshot);
  });

  it('ignores task outputs in the snapshot of a task-level error', () => {
    const error = createTemplateValidationError(template, 'task-1', 'Unknown variable');
    const changedOutputs = { ...template, tasks: [{ ...task, fields: [] }] };

    expect(createTemplateValidationError(changedOutputs, 'task-1', 'Unknown variable')?.entitySnapshot).toBe(
      error?.entitySnapshot,
    );
  });

  it('snapshots only the matching rule of a predicate error', () => {
    const condition = makeCondition('condition-multi', EConditionAction.SkipTask, 'predicate-a');
    const multiRuleCondition = {
      ...condition,
      rules: [...condition.rules, { ...condition.rules[0], ruleApiName: 'rule-b', predicateApiName: 'predicate-b' }],
    } as ICondition;
    const withCondition = (conditions: ICondition[]) => ({ ...template, tasks: [{ ...task, conditions }] });
    const editedSibling = {
      ...multiRuleCondition,
      rules: multiRuleCondition.rules.map((rule) =>
        rule.predicateApiName === 'predicate-b' ? { ...rule, value: 'changed' } : rule,
      ),
    } as ICondition;

    expect(
      createTemplateValidationError(withCondition([editedSibling]), 'predicate-a', 'Fill in')?.entitySnapshot,
    ).toBe(
      createTemplateValidationError(withCondition([multiRuleCondition]), 'predicate-a', 'Fill in')?.entitySnapshot,
    );
  });
});
