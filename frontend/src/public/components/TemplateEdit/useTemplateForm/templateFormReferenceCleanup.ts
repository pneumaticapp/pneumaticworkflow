import { IKickoff, ITemplate } from '../../../types/template';
import { cleanTemplateReferences } from '../../../utils/template';

function getKickoffFieldApiNames(kickoff: IKickoff): string[] {
  return (kickoff.fields || [])
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

export function shouldRunReferenceCleanup(field: string, previous: ITemplate, next: ITemplate): boolean {
  if (field === 'tasks' || field.startsWith('tasks.')) {
    return true;
  }

  if (field === 'kickoff') {
    return didKickoffFieldsChange(previous.kickoff, next.kickoff);
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
