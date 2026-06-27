/* eslint-disable */
/* prettier-ignore */
import { ITemplateClient, ITemplateTaskClient, IKickoffClient, IFieldsetData, IExtraField } from '../../../types/template';
import { setPerformersCounts } from '../../../utils/template';
import { IRunWorkflow } from '../../WorkflowEditPopup/types';
import { normalizeSelections } from './normalizeSelections';

export type TTemplateToRunWorkflow = Pick<
  ITemplateClient,
  'id' | 'name' | 'kickoff' | 'description' | 'isActive' | 'wfNameTemplate'
> & {
  tasks: Pick<ITemplateTaskClient, 'rawPerformers'>[];
};

import { getDataset } from '../../../api/datasets/getDataset';

function getKickoffDatasetIds(kickoff: IKickoffClient, fieldsets: IFieldsetData[] = []): number[] {
  const ids = new Set<number>();
  for (const field of kickoff.fields) {
    if (field.dataset) ids.add(field.dataset);
  }
  for (const fs of fieldsets) {
    for (const field of fs.fields) {
      if (field.dataset) ids.add(field.dataset);
    }
  }
  return [...ids];
}

export async function loadDatasetsMap(kickoff: IKickoffClient, fieldsets: IFieldsetData[] = []): Promise<Record<number, string[]>> {
  const datasetIds = getKickoffDatasetIds(kickoff, fieldsets);
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


function applyDatasetsToFields(fields: IExtraField[], datasetsMap: Record<number, string[]>): IExtraField[] {
  return fields.map((field) => ({
    ...field,
    selections: field.dataset
      ? datasetsMap[field.dataset] || []
      : normalizeSelections(field.selections),
  }));
}

function convertSelectionsToValues(kickoff: IKickoffClient, datasetsMap: Record<number, string[]>): IKickoffClient {
  return {
    ...kickoff,
    fields: applyDatasetsToFields(kickoff.fields, datasetsMap),
  };
}

export const getRunnableWorkflow = (
  template: TTemplateToRunWorkflow,
  datasetsMap: Record<number, string[]> = {},
  loadedFieldsets: IFieldsetData[] = [],
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
    loadedFieldsets: loadedFieldsets.map((fs) => ({
      ...fs,
      fields: applyDatasetsToFields(fs.fields, datasetsMap),
    })),
  };
};

