import { ITemplateTaskClient } from '../../../../../types/template';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';
import { EConditionAction, EConditionLogicOperations, EConditionOperators } from '../../../TaskForm/Conditions';
import { EStartingType } from '../../../TaskForm/Conditions/utils/getDropdownOperators';
import { getStartTaskConditions } from '../../../TaskForm/Conditions/utils/getStartTaskConditions';
import { IGraphNewTaskDraft } from '../../types';
import { KICKOFF_NODE_ID } from '../graphConstants';
import { insertGraphTask } from '../insertGraphTask';

function createTask(overrides: Partial<ITemplateTaskClient> = {}): ITemplateTaskClient {
  return {
    apiName: 'task-a',
    name: 'Task A',
    description: '',
    number: 1,
    requireCompletionByAll: false,
    skipForStarter: false,
    fields: [],
    fieldsets: [],
    rawPerformers: [],
    delay: null,
    rawDueDate: createEmptyTaskDueDate(),
    conditions: [],
    uuid: 'uuid-a',
    checklists: [],
    revertTask: null,
    ancestors: [],
    ...overrides,
  };
}

function createFromDraft(draft: IGraphNewTaskDraft): ITemplateTaskClient {
  return createTask({
    apiName: 'task-new',
    uuid: 'uuid-new',
    name: draft.name,
    number: draft.number,
    conditions: draft.conditions,
  });
}

function startRules(task: ITemplateTaskClient) {
  const start = task.conditions.find((condition) => condition.action === EConditionAction.StartTask);

  return start?.rules ?? [];
}

describe('insertGraphTask', () => {
  it('should append a task that starts after the leaf card', () => {
    const tasks = [createTask()];
    const result = insertGraphTask(
      tasks,
      { kind: 'continue', afterId: 'task-a' },
      createFromDraft,
    );
    const created = result.tasks.find((task) => task.apiName === 'task-new');
    const createdRules = created ? startRules(created) : [];

    expect(result.createdApiName).toBe('task-new');
    expect(result.tasks).toHaveLength(2);
    expect(created?.name).toBe('New Step 2');
    expect(created?.number).toBe(2);
    expect(createdRules).toHaveLength(1);
    expect(createdRules[0].field).toBe('task-a');
    expect(createdRules[0].fieldType).toBe(EStartingType.Task);
  });

  it('should append a task that starts after kickoff', () => {
    const result = insertGraphTask(
      [],
      { kind: 'continue', afterId: KICKOFF_NODE_ID },
      createFromDraft,
    );
    const createdRules = startRules(result.tasks[0]);

    expect(result.tasks).toHaveLength(1);
    expect(createdRules).toHaveLength(1);
    expect(createdRules[0].fieldType).toBe(EStartingType.Kickoff);
    expect(createdRules[0].operator).toBe(EConditionOperators.Completed);
  });

  it('should insert a task between A and B and retarget B start-after', () => {
    const taskA = createTask();
    const taskB = createTask({
      apiName: 'task-b',
      name: 'Task B',
      number: 2,
      uuid: 'uuid-b',
      conditions: getStartTaskConditions('task-a'),
    });
    const result = insertGraphTask(
      [taskA, taskB],
      { kind: 'insert', afterId: 'task-a', beforeId: 'task-b' },
      createFromDraft,
    );
    const created = result.tasks.find((task) => task.apiName === 'task-new');
    const nextB = result.tasks.find((task) => task.apiName === 'task-b');

    expect(result.tasks.map((task) => task.apiName)).toEqual(['task-a', 'task-new', 'task-b']);
    expect(created?.number).toBe(2);
    expect(nextB?.number).toBe(3);
    expect(startRules(created as ITemplateTaskClient)[0].field).toBe('task-a');
    expect(startRules(nextB as ITemplateTaskClient)[0].field).toBe('task-new');
  });

  it('should replace only the matching start-after source on a join', () => {
    const taskB = createTask({
      apiName: 'task-b',
      name: 'Task B',
      number: 3,
      uuid: 'uuid-b',
      conditions: [
        {
          apiName: 'start-b',
          order: 1,
          action: EConditionAction.StartTask,
          rules: [
            {
              ruleApiName: 'from-a',
              predicateApiName: 'pred-a',
              field: 'task-a',
              fieldType: EStartingType.Task,
              operator: EConditionOperators.Completed,
              logicOperation: EConditionLogicOperations.And,
            },
            {
              ruleApiName: 'from-c',
              predicateApiName: 'pred-c',
              field: 'task-c',
              fieldType: EStartingType.Task,
              operator: EConditionOperators.Completed,
              logicOperation: EConditionLogicOperations.And,
            },
          ],
        },
      ],
    });
    const result = insertGraphTask(
      [
        createTask(),
        createTask({ apiName: 'task-c', name: 'Task C', number: 2, uuid: 'uuid-c' }),
        taskB,
      ],
      { kind: 'insert', afterId: 'task-a', beforeId: 'task-b' },
      createFromDraft,
    );
    const nextBRules = startRules(result.tasks.find((task) => task.apiName === 'task-b') as ITemplateTaskClient);
    const fields = nextBRules.map((rule) => rule.field);

    expect(fields).toContain('task-new');
    expect(fields).toContain('task-c');
    expect(fields).not.toContain('task-a');
  });

  it('should set start-after on B when it had no StartTask rule', () => {
    const skipCondition = {
      apiName: 'skip-b',
      order: 1,
      action: EConditionAction.SkipTask,
      rules: [
        {
          ruleApiName: 'skip-rule',
          predicateApiName: 'skip-pred',
          field: 'field-1',
          operator: EConditionOperators.Exist,
          logicOperation: EConditionLogicOperations.And,
        },
      ],
    };
    const taskB = createTask({
      apiName: 'task-b',
      name: 'Task B',
      number: 2,
      uuid: 'uuid-b',
      conditions: [skipCondition],
    });
    const result = insertGraphTask(
      [createTask(), taskB],
      { kind: 'insert', afterId: 'task-a', beforeId: 'task-b' },
      createFromDraft,
    );
    const nextB = result.tasks.find((task) => task.apiName === 'task-b') as ITemplateTaskClient;
    const start = nextB.conditions.find((condition) => condition.action === EConditionAction.StartTask);
    const skip = nextB.conditions.find((condition) => condition.action === EConditionAction.SkipTask);

    expect(start?.rules[0].field).toBe('task-new');
    expect(skip).toEqual(skipCondition);
  });

  it('should leave tasks unchanged when the before card is missing', () => {
    const tasks = [createTask()];
    const result = insertGraphTask(
      tasks,
      { kind: 'insert', afterId: 'task-a', beforeId: 'missing' },
      createFromDraft,
    );

    expect(result.createdApiName).toBeNull();
    expect(result.tasks).toBe(tasks);
  });
});
