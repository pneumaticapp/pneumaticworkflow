import type { IFieldsetBindingClient, IFieldsetField } from '../../types/fieldset';
import type { IExtraField, ITemplateClient, ITemplateTaskClient } from '../../types/template';
import { ETaskFormParts } from '../../components/TemplateEdit/types';
import { EConditionAction } from '../../components/TemplateEdit/TaskForm/Conditions/types';
import type { ITemplateValidationError, ITemplateValidationErrorMatch } from './types';

const hasSelection = (field: IExtraField | IFieldsetField, apiName: string) =>
  (field.selections || []).some((selection) => typeof selection !== 'string' && selection.apiName === apiName);

const findField = (fields: IExtraField[], apiName: string) =>
  fields.find((field) => field.apiName === apiName || hasSelection(field, apiName));

const findFieldset = (fieldsets: IFieldsetBindingClient[], apiName: string) =>
  fieldsets.find(
    (fieldset) =>
      fieldset.apiNameBinding === apiName ||
      fieldset.fields.some((field) => field.apiName === apiName || hasSelection(field, apiName)) ||
      fieldset.rules.some((rule) => rule.apiName === apiName),
  );

const getTaskOwnProperties = ({
  name,
  description,
  delay,
  rawPerformers,
  revertTask,
  conditions,
}: ITemplateTaskClient) => ({
  name,
  description,
  delay,
  rawPerformers,
  revertTask,
  conditions,
});

const findInTask = (
  task: ITemplateTaskClient,
  apiName: string,
  taskSection: ETaskFormParts | null,
): ITemplateValidationErrorMatch | null => {
  const inTask = (section: ETaskFormParts | null, elementApiName: string, entity: unknown) => ({
    target: { taskUuid: task.uuid, section, elementApiName },
    entity,
  });

  if (task.apiName === apiName) {
    return taskSection === ETaskFormParts.AssignPerformers
      ? inTask(taskSection, task.apiName, task.rawPerformers)
      : inTask(null, task.apiName, getTaskOwnProperties(task));
  }

  if (task.rawPerformers.some((performer) => performer.apiName === apiName)) {
    return inTask(ETaskFormParts.AssignPerformers, task.apiName, task.rawPerformers);
  }

  const field = findField(task.fields, apiName);
  if (field) return inTask(ETaskFormParts.Fields, field.apiName, field);

  const fieldset = findFieldset(task.fieldsets || [], apiName);
  if (fieldset) return inTask(ETaskFormParts.Fields, fieldset.apiNameBinding, fieldset);

  const condition = task.conditions.find(
    (item) => item.apiName === apiName || item.rules.some((rule) => rule.ruleApiName === apiName),
  );
  const predicateCondition = task.conditions.find((item) =>
    item.rules.some((rule) => rule.predicateApiName === apiName),
  );
  const matchedCondition = condition || predicateCondition;
  if (matchedCondition) {
    const section =
      matchedCondition.action === EConditionAction.StartTask ? ETaskFormParts.StartsAfter : ETaskFormParts.CheckIf;

    return inTask(section, condition ? condition.apiName : apiName, matchedCondition);
  }

  if (task.rawDueDate?.apiName === apiName) return inTask(ETaskFormParts.DueIn, apiName, task.rawDueDate);

  const checklist = task.checklists.find(
    (item) => item.apiName === apiName || item.selections.some((selection) => selection.apiName === apiName),
  );
  if (checklist) return inTask(null, apiName, checklist);

  return null;
};

const SNAPSHOT_IGNORED_KEYS = ['id', 'order', 'ancestors'];

const normalizeSnapshotValue = (value: unknown): unknown => {
  if (Array.isArray(value)) return value.map(normalizeSnapshotValue);
  if (!value || typeof value !== 'object') return value;

  return Object.keys(value)
    .filter((key) => !SNAPSHOT_IGNORED_KEYS.includes(key))
    .sort()
    .reduce<Record<string, unknown>>((result, key) => {
      result[key] = normalizeSnapshotValue((value as Record<string, unknown>)[key]);

      return result;
    }, {});
};

export const getValidationErrorEntitySnapshot = (entity: unknown) => JSON.stringify(normalizeSnapshotValue(entity));

export function getValidationErrorTarget(
  template: ITemplateClient,
  apiName: string,
  taskSection: ETaskFormParts | null = null,
): ITemplateValidationErrorMatch | null {
  const { kickoff, tasks } = template;
  const kickoffElement = findField(kickoff.fields, apiName) || findFieldset(kickoff.fieldsets || [], apiName);

  if (kickoffElement) {
    const elementApiName = 'apiNameBinding' in kickoffElement ? kickoffElement.apiNameBinding : kickoffElement.apiName;

    return { target: { taskUuid: null, section: null, elementApiName }, entity: kickoffElement };
  }

  return tasks.reduce<ITemplateValidationErrorMatch | null>(
    (match, task) => match || findInTask(task, apiName, taskSection),
    null,
  );
}

export function createTemplateValidationError(
  template: ITemplateClient,
  apiName: string,
  message: string,
  taskSection: ETaskFormParts | null = null,
): ITemplateValidationError | null {
  const match = getValidationErrorTarget(template, apiName, taskSection);
  if (!match) return null;

  return { apiName, message, target: match.target, entitySnapshot: getValidationErrorEntitySnapshot(match.entity) };
}
