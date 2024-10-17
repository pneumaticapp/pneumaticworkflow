/* eslint-disable */
/* prettier-ignore */
import { ITemplate, ITemplateTask } from '../../../types/template';
import { IRunWorkflow } from '../../WorkflowEditPopup/types';

type TTemplateToRunWorkflow = Pick<ITemplate,
| 'id'
| 'name'
| 'kickoff'
| 'description'
| 'isActive'
| 'wfNameTemplate'
> & {
  tasks: Pick<ITemplateTask, 'rawPerformers'>[];
};

export const getRunnableWorkflow = (template: TTemplateToRunWorkflow): IRunWorkflow | null => {
  const { id, name, kickoff, description, isActive, tasks, wfNameTemplate } = template;

  if (!isActive || !id) {
    return null;
  }

  const performersCount = tasks
    .reduce((acc, { rawPerformers }) => [...acc, ...rawPerformers], [])
    .filter((performer, index, allPerformers) => {
      const firstIndex = allPerformers
        .findIndex(p => p.type === performer.type && (!performer.sourceId || p.sourceId === performer.sourceId));

      return firstIndex === index;
    })
    .length;

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
