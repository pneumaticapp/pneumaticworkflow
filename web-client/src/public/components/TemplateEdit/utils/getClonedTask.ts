import {
  IDueDate,
  IExtraField,
  IExtraFieldSelection,
  ITemplateTask,
  TOutputChecklist,
  TOutputChecklistItem,
} from '../../../types/template';
import {
  createTaskApiName,
  createFieldApiName,
  createFieldSelectionApiName,
  createConditionApiName,
  createConditionRuleApiName,
  createConditionPredicateApiName,
  createUUID,
  createСhecklistApiName,
  createСhecklistSelectionApiName,
  createDueDateApiName,
} from '../../../utils/createId';
import { omit } from '../../../utils/helpers';
import { ICondition, TConditionRule } from '../TaskForm/Conditions';

export function getClonedTask(task: ITemplateTask) {
  const mapChecklist: { [old: string]: string } = {};
  const mapSelectionsСhecklist: { [old: string]: string } = {};

  const cloneFields = (fields: IExtraField[]): IExtraField[] => {
    return fields.map((field) => ({
      ...omit(field, ['id', 'apiName', 'selections']),
      apiName: createFieldApiName(),
      selections: cloneSelections(field.selections),
    }));
  };

  const cloneSelections = (selections: IExtraFieldSelection[] | undefined): IExtraFieldSelection[] | undefined => {
    if (!selections) {
      return undefined;
    }

    return selections.map((selection) => ({ ...omit(selection, ['apiName']), apiName: createFieldSelectionApiName() }));
  };

  const cloneConditions = (conditions: ICondition[]): ICondition[] => {
    return conditions.map((condition) => ({
      ...omit(condition, ['id', 'apiName', 'rules']),
      apiName: createConditionApiName(),
      rules: cloneConditionRules(condition.rules),
    }));
  };

  const cloneConditionRules = (rules: TConditionRule[]): TConditionRule[] => {
    const rulesDictionary = new Map();

    const newRules: TConditionRule[] = rules.map((rule) => {
      if (!rulesDictionary.get(rule.ruleApiName)) {
        rulesDictionary.set(rule.ruleApiName, createConditionRuleApiName());
      }

      return {
        ...rule,
        ruleId: undefined,
        predicateId: undefined,
        ruleApiName: rulesDictionary.get(rule.ruleApiName),
        predicateApiName: createConditionPredicateApiName(),
      };
    });

    return newRules;
  };

  const cloneSelectionsСhecklist = (selections: TOutputChecklistItem[]): TOutputChecklistItem[] => {
    return selections.map((selection) => {
      const newApiName = createСhecklistSelectionApiName();
      mapSelectionsСhecklist[selection.apiName] = newApiName;

      return {
        ...omit(selection, ['apiName']),
        apiName: newApiName,
      };
    });
  };

  const cloneChecklists = (checklists: TOutputChecklist[]): TOutputChecklist[] => {
    return checklists.map((checklist) => {
      const newApiName = createСhecklistApiName();
      mapChecklist[checklist.apiName] = newApiName;

      return {
        ...omit(checklist, ['apiName', 'selections']),
        apiName: newApiName,
        selections: cloneSelectionsСhecklist(checklist.selections),
      };
    });
  };

  const cloneDescription = (description: string): string => {
    let descriptionWithReplaceApiNameCheckist: string = description;

    Object.entries(mapChecklist).forEach(([key, value]) => {
      descriptionWithReplaceApiNameCheckist = descriptionWithReplaceApiNameCheckist.replaceAll(key, value);
    });

    Object.entries(mapSelectionsСhecklist).forEach(([key, value]) => {
      descriptionWithReplaceApiNameCheckist = descriptionWithReplaceApiNameCheckist.replaceAll(key, value);
    });

    return descriptionWithReplaceApiNameCheckist;
  };

  const cloneRawDueDate = (rawDueDate: IDueDate): IDueDate => {
    return {
      ...omit(rawDueDate, ['apiName']),
      apiName: createDueDateApiName(),
    };
  };

  const clonedChecklist = cloneChecklists(task.checklists);
  const clonedDescription = cloneDescription(task.description);
  const clonedRawDueDate = cloneRawDueDate(task.rawDueDate);

  const clonedTask: ITemplateTask = {
    ...omit(task, ['id', 'apiName', 'uuid', 'fields', 'conditions', 'delay', 'name', 'description', 'rawDueDate']),
    name: `${task.name} (Clone)`,
    checklists: clonedChecklist,
    description: clonedDescription,
    apiName: createTaskApiName(),
    uuid: createUUID(),
    fields: cloneFields(task.fields),
    conditions: cloneConditions(task.conditions),
    delay: null,
    rawDueDate: clonedRawDueDate
  };

  return clonedTask;
}
