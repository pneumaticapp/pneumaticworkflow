/* eslint-disable */
/* prettier-ignore */
import { ITemplate, ITemplateTask } from '../../../types/template';
import { setPerformersCounts } from '../../../utils/template';
import { IRunWorkflow } from '../../WorkflowEditPopup/types';

type TTemplateToRunWorkflow = Pick<
  ITemplate,
  'id' | 'name' | 'kickoff' | 'description' | 'isActive' | 'wfNameTemplate'
> & {
  tasks: Pick<ITemplateTask, 'rawPerformers'>[];
};

export const getRunnableWorkflow = (template: TTemplateToRunWorkflow): IRunWorkflow | null => {
  const { id, name, kickoff, description, isActive, tasks, wfNameTemplate } = template;
  if (!isActive || !id) {
    return null;
  }
  const performersCount = setPerformersCounts(tasks);

  return {
    id,
    name,
    kickoff,
    description,
    performersCount,
    tasksCount: tasks.length,
    wfNameTemplate,
  };
};
