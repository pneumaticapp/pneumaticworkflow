/// <reference types="jest" />
import { EExtraFieldType, ITemplate, ITemplateTask } from '../../../../types/template';
import { EConditionAction, EConditionLogicOperations } from '../../TaskForm/Conditions/types';
import { collectTemplateValidationErrors } from '../collectTemplateValidationErrors';

const makeTask = (overrides: Partial<ITemplateTask> = {}): ITemplateTask =>
  ({
    apiName: 'task-1',
    number: 1,
    uuid: 'uuid-1',
    name: 'Task 1',
    description: '',
    fields: [],
    conditions: [],
    rawPerformers: [{ type: 'user', sourceId: '1', apiName: 'perf-1' }],
    rawDueDate: { duration: '', rule: 'after task started', apiName: 'due-1' },
    delay: null,
    checklists: [],
    requireCompletionByAll: false,
    skipForStarter: false,
    revertTask: null,
    ancestors: [],
    ...overrides,
  }) as ITemplateTask;

const makeTemplate = (overrides: Partial<ITemplate> = {}): ITemplate =>
  ({
    id: 1,
    name: 'Template',
    description: '',
    isActive: false,
    finalizable: false,
    completionNotification: false,
    reminderNotification: false,
    dateUpdated: null,
    updatedBy: null,
    owners: [{ sourceId: '1', type: 'user', role: 'owner', apiName: 'owner-1' }],
    kickoff: { description: '', fields: [] },
    tasks: [makeTask()],
    isPublic: false,
    publicUrl: null,
    publicSuccessUrl: null,
    isEmbedded: false,
    embedUrl: null,
    wfNameTemplate: null,
    tasksCount: 1,
    performersCount: 1,
    ...overrides,
  }) as ITemplate;

describe('collectTemplateValidationErrors', () => {
  it('returns a name error with scroll target on the template title', () => {
    const { blockingErrors } = collectTemplateValidationErrors(makeTemplate({ name: '' }), true);

    expect(blockingErrors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: 'name',
          messageId: 'validation.process-name-empty',
          scrollTarget: { area: 'name' },
        }),
      ]),
    );
  });

  it('returns an owners error when there are no owners', () => {
    const { blockingErrors } = collectTemplateValidationErrors(makeTemplate({ owners: [] }), true);

    expect(blockingErrors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: 'owners',
          scrollTarget: { area: 'owners' },
        }),
      ]),
    );
  });

  it('returns kickoff field errors with field-specific paths', () => {
    const { blockingErrors } = collectTemplateValidationErrors(
      makeTemplate({
        kickoff: {
          description: '',
          fields: [
            {
              apiName: 'kickoff-field',
              name: '',
              type: EExtraFieldType.String,
              order: 1,
              userId: null,
              groupId: null,
            },
          ],
        },
      }),
      true,
    );

    expect(blockingErrors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: 'kickoff.fields.kickoff-field.name',
          scrollTarget: { area: 'kickoff', fieldApiName: 'kickoff-field' },
        }),
      ]),
    );
  });

  it('returns condition rule errors with task and form part metadata', () => {
    const { blockingErrors } = collectTemplateValidationErrors(
      makeTemplate({
        tasks: [
          makeTask({
            conditions: [
              {
                apiName: 'condition-1',
                order: 1,
                action: EConditionAction.SkipTask,
                rules: [
                  {
                    ruleApiName: 'rule-1',
                    predicateApiName: 'predicate-1',
                    logicOperation: EConditionLogicOperations.And,
                    field: 'some-field',
                    fieldType: EExtraFieldType.String,
                    operator: null,
                    value: null,
                  },
                ],
              },
            ],
          }),
        ],
      }),
      true,
    );

    expect(blockingErrors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: 'tasks.uuid-1.conditions.condition-1.rules.rule-1.operator',
          messageId: 'template.validation.condition-operator-required',
          scrollTarget: expect.objectContaining({
            area: 'task',
            taskUuid: 'uuid-1',
            ruleApiName: 'rule-1',
          }),
        }),
      ]),
    );
  });
});
