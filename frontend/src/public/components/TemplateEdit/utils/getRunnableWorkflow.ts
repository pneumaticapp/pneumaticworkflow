/* eslint-disable */
/* prettier-ignore */
import { ITemplate, ITemplateTask, IExtraFieldSelection, IKickoff } from '../../../types/template';
import { setPerformersCounts } from '../../../utils/template';
import { IRunWorkflow } from '../../WorkflowEditPopup/types';

type TTemplateToRunWorkflow = Pick<
  ITemplate,
  'id' | 'name' | 'kickoff' | 'description' | 'isActive' | 'wfNameTemplate'
> & {
  tasks: Pick<ITemplateTask, 'rawPerformers'>[];
};

import { getDataset } from '../../../api/datasets/getDataset';

function getKickoffDatasetIds(kickoff: IKickoff): number[] {
  const ids = new Set<number>();
  for (const field of kickoff.fields) {
    if (field.dataset) ids.add(field.dataset);
  }
  return [...ids];
}

export async function loadDatasetsMap(kickoff: IKickoff): Promise<Record<number, string[]>> {
  const datasetIds = getKickoffDatasetIds(kickoff);
  if (datasetIds.length === 0) {
    return {};
  }

  const datasets = await Promise.all(
    datasetIds.map((id) => getDataset({ id })),
  );

  const datasetsMap: Record<number, string[]> = {};
  datasetIds.forEach((id, i) => {
    datasetsMap[id] = datasets[i].items.map((item) => item.value);
  });

  return datasetsMap;
}

export function normalizeSelections(selections?: IExtraFieldSelection[] | string[]): string[] {
  if (!selections?.length) return [];
  if (typeof selections[0] === 'string') return selections as string[];
  return (selections as IExtraFieldSelection[]).map((item) => item.value);
}

function convertSelectionsToValues(kickoff: IKickoff, datasetsMap: Record<number, string[]>): IKickoff {
  return {
    ...kickoff,
    fields: kickoff.fields.map((field) => ({
      ...field,
      selections: field.dataset
        ? datasetsMap[field.dataset] || []
        : normalizeSelections(field.selections),
    })),
  };
}

export const getRunnableWorkflow = (
  template: TTemplateToRunWorkflow,
  datasetsMap: Record<number, string[]> = {},
): IRunWorkflow | null => {
  const { id, name, kickoff, description, isActive, tasks, wfNameTemplate } = template;
  if (!isActive || !id) {
    return null;
  }
  const performersCount = setPerformersCounts(tasks);

  return {
    id,
    name,
    kickoff: convertSelectionsToValues(kickoff, datasetsMap),
    description,
    performersCount,
    tasksCount: tasks.length,
    wfNameTemplate,
  };
};
