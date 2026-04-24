/* eslint-disable */
/* prettier-ignore */
import { ITemplate, ITemplateTask, IKickoff, IFieldsetData, IExtraField } from '../../../types/template';
import { setPerformersCounts } from '../../../utils/template';
import { IRunWorkflow } from '../../WorkflowEditPopup/types';
import { normalizeSelections } from './normalizeSelections';

type TTemplateToRunWorkflow = Pick<
  ITemplate,
  'id' | 'name' | 'kickoff' | 'description' | 'isActive' | 'wfNameTemplate'
> & {
  tasks: Pick<ITemplateTask, 'rawPerformers'>[];
};

import { getDataset } from '../../../api/datasets/getDataset';
import { getFieldset } from '../../../api/fieldsets/getFieldset';
import { mapFieldsetTemplateToFieldsetData } from '../../../utils/mapFieldsetTemplateToFieldsetData';

function getKickoffDatasetIds(kickoff: IKickoff, fieldsets: IFieldsetData[] = []): number[] {
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

export async function loadDatasetsMap(kickoff: IKickoff, fieldsets: IFieldsetData[] = []): Promise<Record<number, string[]>> {
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

export async function loadFieldsetsData(kickoff: IKickoff): Promise<IFieldsetData[]> {
  const fieldsetIds = kickoff.fieldsets || [];
  if (fieldsetIds.length === 0) {
    return [];
  }

  // If fieldsets are full objects (from list API), map them directly
  if (typeof fieldsetIds[0] !== 'number') {
    return (fieldsetIds as any[]).map(mapFieldsetTemplateToFieldsetData);
  }

  const fieldsetTemplates = await Promise.all(
    fieldsetIds.map((id) => getFieldset({ id: id as number })),
  );

  return fieldsetTemplates.map(mapFieldsetTemplateToFieldsetData);
}


function applyDatasetsToFields(fields: IExtraField[], datasetsMap: Record<number, string[]>): IExtraField[] {
  return fields.map((field) => ({
    ...field,
    selections: field.dataset
      ? datasetsMap[field.dataset] || []
      : normalizeSelections(field.selections),
  }));
}

function convertSelectionsToValues(kickoff: IKickoff, datasetsMap: Record<number, string[]>): IKickoff {
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

