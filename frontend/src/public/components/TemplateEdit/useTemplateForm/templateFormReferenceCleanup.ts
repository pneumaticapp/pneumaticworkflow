import { IKickoffClient, ITemplateClient, ITemplateTaskClient } from '../../../types/template';
import { cleanTemplateReferences } from '../../../utils/template';

function getKickoffFieldApiNames(kickoff: IKickoffClient): string[] {
  return (kickoff.fields || [])
    .map((field) => field.apiName)
    .filter(Boolean)
    .sort();
}

function getTaskOutputFieldApiNames(task: ITemplateTaskClient | undefined): string[] {
  return (task?.fields || [])
    .map((field) => field.apiName)
    .filter(Boolean)
    .sort();
}

function didKickoffFieldsChange(previous: IKickoffClient, next: IKickoffClient): boolean {
  const previousNames = getKickoffFieldApiNames(previous);
  const nextNames = getKickoffFieldApiNames(next);

  return previousNames.length !== nextNames.length
    || previousNames.some((name, index) => name !== nextNames[index]);
}

function didTaskOutputFieldsChange(previousTask: ITemplateTaskClient | undefined, nextTask: ITemplateTaskClient | undefined): boolean {
  const previousNames = getTaskOutputFieldApiNames(previousTask);
  const nextNames = getTaskOutputFieldApiNames(nextTask);

  return previousNames.length !== nextNames.length
    || previousNames.some((name, index) => name !== nextNames[index]);
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
