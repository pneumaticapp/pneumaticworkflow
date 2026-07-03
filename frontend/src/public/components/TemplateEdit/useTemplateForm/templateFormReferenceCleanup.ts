import { IKickoff, ITemplate, ITemplateTask } from '../../../types/template';
import { cleanTemplateReferences } from '../../../utils/template';

function getKickoffFieldApiNames(kickoff: IKickoff): string[] {
  return (kickoff.fields || [])
    .map((field) => field.apiName)
    .filter(Boolean)
    .sort();
}

function getTaskOutputFieldApiNames(task: ITemplateTask | undefined): string[] {
  return (task?.fields || [])
    .map((field) => field.apiName)
    .filter(Boolean)
    .sort();
}

function didKickoffFieldsChange(previous: IKickoff, next: IKickoff): boolean {
  const previousNames = getKickoffFieldApiNames(previous);
  const nextNames = getKickoffFieldApiNames(next);

  return previousNames.length !== nextNames.length
    || previousNames.some((name, index) => name !== nextNames[index]);
}

function didTaskOutputFieldsChange(previousTask: ITemplateTask | undefined, nextTask: ITemplateTask | undefined): boolean {
  const previousNames = getTaskOutputFieldApiNames(previousTask);
  const nextNames = getTaskOutputFieldApiNames(nextTask);

  return previousNames.length !== nextNames.length
    || previousNames.some((name, index) => name !== nextNames[index]);
}

export function shouldRunReferenceCleanup(field: string, previous: ITemplate, next: ITemplate): boolean {
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

export function applyReferenceCleanup(template: ITemplate): ITemplate {
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
