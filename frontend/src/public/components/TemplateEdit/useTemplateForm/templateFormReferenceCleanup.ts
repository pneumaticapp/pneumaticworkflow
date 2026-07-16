import { IFieldsetBindingClient } from '../../../types/fieldset';
import { IExtraField, IKickoffClient, ITemplateClient, ITemplateTaskClient } from '../../../types/template';
import { cleanTemplateReferences } from '../../../utils/template';

type TOutputField = Pick<IExtraField, 'apiName'>;

function getOutputFieldApiNames(
  fields: TOutputField[] | undefined,
  fieldsets: Pick<IFieldsetBindingClient, 'fields'>[] | undefined,
): string[] {
  return [
    ...(fields || []),
    ...(fieldsets || []).flatMap((fieldset) => fieldset.fields || []),
  ]
    .map((field) => field.apiName)
    .filter(Boolean)
    .sort();
}

function getKickoffFieldApiNames(kickoff: IKickoffClient): string[] {
  return getOutputFieldApiNames(kickoff.fields, kickoff.fieldsets);
}

function getTaskOutputFieldApiNames(task: ITemplateTaskClient | undefined): string[] {
  return getOutputFieldApiNames(task?.fields, task?.fieldsets);
}

function haveApiNamesChanged(previousNames: string[], nextNames: string[]): boolean {
  return previousNames.length !== nextNames.length
    || previousNames.some((name, index) => name !== nextNames[index]);
}

function didKickoffFieldsChange(previous: IKickoffClient, next: IKickoffClient): boolean {
  return haveApiNamesChanged(getKickoffFieldApiNames(previous), getKickoffFieldApiNames(next));
}

function didTaskOutputFieldsChange(previousTask: ITemplateTaskClient | undefined, nextTask: ITemplateTaskClient | undefined): boolean {
  return haveApiNamesChanged(getTaskOutputFieldApiNames(previousTask), getTaskOutputFieldApiNames(nextTask));
}

export function shouldRunReferenceCleanup(field: string, previous: ITemplateClient, next: ITemplateClient): boolean {
  if (field === 'tasks') {
    return true;
  }

  if (field === 'kickoff') {
    return didKickoffFieldsChange(previous.kickoff, next.kickoff);
  }

  const taskFieldsMatch = /^tasks\.(\d+)\.fields$/.exec(field);
  if (taskFieldsMatch) {
    return true;
  }

  const taskFieldsetsMatch = /^tasks\.(\d+)\.fieldsets$/.exec(field);
  if (taskFieldsetsMatch) {
    const taskIndex = Number(taskFieldsetsMatch[1]);
    return didTaskOutputFieldsChange(previous.tasks[taskIndex], next.tasks[taskIndex]);
  }

  const wholeTaskMatch = /^tasks\.(\d+)$/.exec(field);
  if (wholeTaskMatch) {
    const taskIndex = Number(wholeTaskMatch[1]);
    return didTaskOutputFieldsChange(previous.tasks[taskIndex], next.tasks[taskIndex]);
  }

  return false;
}

export function applyReferenceCleanup(template: ITemplateClient): ITemplateClient {
  const cleaned = cleanTemplateReferences(template);
  const wfNameTemplate = template.wfNameTemplate == null && cleaned.wfNameTemplate === ''
    ? template.wfNameTemplate
    : cleaned.wfNameTemplate;

  return {
    ...template,
    tasks: cleaned.tasks,
    wfNameTemplate,
  };
}
