import { ITemplateClient, ITemplateTaskClient } from '../../../types/template';
import { getTemplateIdFromUrl } from '../../../utils/template';

export function resolveTemplateFormIdentity(
  template: ITemplateClient,
  location: { pathname: string; search: string },
): string | number | undefined {
  if (template.id) {
    return template.id;
  }

  const systemTemplateId = getTemplateIdFromUrl(location.search);
  if (systemTemplateId) {
    return `create:system:${systemTemplateId}`;
  }

  return `create:${location.pathname}`;
}

export function setNestedFieldValue(obj: ITemplateClient, path: string, value: unknown): ITemplateClient {
  const taskPathMatch = path.match(/^tasks\.(\d+)(?:\.(.+))?$/);

  if (taskPathMatch) {
    const index = Number(taskPathMatch[1]);
    const taskField = taskPathMatch[2];
    const tasks = [...obj.tasks];

    if (!taskField) {
      tasks[index] = value as ITemplateTaskClient;
    } else {
      tasks[index] = {
        ...tasks[index],
        [taskField]: value,
      };
    }

    return { ...obj, tasks };
  }

  return { ...obj, [path]: value };
}

export function mergePreservedTasks(
  incomingTasks: ITemplateTaskClient[],
  preservedTasks: ITemplateTaskClient[],
  baselineTasks: ITemplateTaskClient[],
): ITemplateTaskClient[] {
  const incomingByUuid = new Map(incomingTasks.map((task) => [task.uuid, task]));
  const baselineUuids = new Set(baselineTasks.map((task) => task.uuid));

  const mergedFromPreserved = preservedTasks.map((preserved) => {
    const incoming = incomingByUuid.get(preserved.uuid);

    if (!incoming || preserved === incoming) {
      return preserved;
    }

    const onlyAncestorsDiffer = (Object.keys(preserved) as (keyof ITemplateTaskClient)[]).every(
      (key) => key === 'ancestors' || preserved[key] === incoming[key],
    );

    return onlyAncestorsDiffer ? { ...preserved, ancestors: incoming.ancestors } : preserved;
  });

  const preservedUuids = new Set(preservedTasks.map((task) => task.uuid));
  const serverAddedTasks = incomingTasks.filter(
    (task) => !baselineUuids.has(task.uuid) && !preservedUuids.has(task.uuid),
  );

  if (serverAddedTasks.length === 0) {
    return mergedFromPreserved;
  }

  const sortedServerAdded = [...serverAddedTasks].sort((a, b) => a.number - b.number);
  const preservedOrderNumber = (task: ITemplateTaskClient) =>
    incomingByUuid.get(task.uuid)?.number ?? task.number;

  const insertState = { serverIndex: 0 };

  const interleaved = mergedFromPreserved.reduce<ITemplateTaskClient[]>((result, preserved) => {
    while (
      insertState.serverIndex < sortedServerAdded.length
      && sortedServerAdded[insertState.serverIndex].number < preservedOrderNumber(preserved)
    ) {
      result.push(sortedServerAdded[insertState.serverIndex]);
      insertState.serverIndex += 1;
    }
    result.push(preserved);
    return result;
  }, []);

  return [...interleaved, ...sortedServerAdded.slice(insertState.serverIndex)];
}

export function applyPendingEdits(
  initialValues: ITemplateClient,
  pendingEdits: Partial<ITemplateClient>,
  baselineValues: ITemplateClient,
): ITemplateClient {
  if (Object.keys(pendingEdits).length === 0) {
    return initialValues;
  }

  let mergedValues: ITemplateClient = { ...initialValues, ...pendingEdits };

  if (pendingEdits.tasks && initialValues.tasks) {
    mergedValues = {
      ...mergedValues,
      tasks: mergePreservedTasks(initialValues.tasks, pendingEdits.tasks, baselineValues.tasks),
    };
  }

  return mergedValues;
}

export function overlayPendingEdits(
  formikValues: ITemplateClient,
  pendingEdits: Partial<ITemplateClient>,
  baselineValues: ITemplateClient,
): ITemplateClient {
  if (Object.keys(pendingEdits).length === 0) {
    return formikValues;
  }

  return applyPendingEdits(formikValues, pendingEdits, baselineValues);
}

export function getChangedFields(previous: ITemplateClient, next: ITemplateClient): Partial<ITemplateClient> {
  const changedFields: Partial<ITemplateClient> = {};

  (Object.keys(next) as (keyof ITemplateClient)[]).forEach((key) => {
    if (previous[key] !== next[key]) {
      (changedFields[key] as ITemplateClient[keyof ITemplateClient]) = next[key];
    }
  });

  return changedFields;
}

export function getUnconsumedPendingEdits(
  consumed: Partial<ITemplateClient>,
  current: Partial<ITemplateClient>,
): Partial<ITemplateClient> {
  const remainder: Partial<ITemplateClient> = {};

  (Object.keys(current) as (keyof ITemplateClient)[]).forEach((key) => {
    // Redux normalization recreates nested arrays/objects after every save.
    // Only keep edits whose value actually changed while the request was in flight.
    if (JSON.stringify(current[key]) !== JSON.stringify(consumed[key])) {
      (remainder[key] as ITemplateClient[keyof ITemplateClient]) = current[key];
    }
  });

  return remainder;
}

export function resolveTemplateIdentity(
  initialValues: ITemplateClient,
  templateIdentityKey?: string | number,
): string | number | undefined {
  if (templateIdentityKey !== undefined) {
    return templateIdentityKey;
  }

  return initialValues.id;
}

/** Stable key for every source property represented in `getVariables()`. */
export function getTemplateVariablesFingerprint(values: ITemplateClient): string {
  const getFieldSignature = (field: ITemplateClient['kickoff']['fields'][number]) => ({
    apiName: field.apiName,
    name: field.name,
    type: field.type,
    selections: field.selections,
    dataset: field.dataset,
  });

  return JSON.stringify({
    id: values.id ?? 'new',
    kickoff: (values.kickoff?.fields ?? []).map(getFieldSignature),
    tasks: values.tasks.map((task) => ({
      uuid: task.uuid,
      name: task.name,
      fields: (task.fields ?? []).map(getFieldSignature),
    })),
  });
}

export function hasTemplateIdentityChanged(
  previousIdentity: string | number | undefined,
  nextIdentity: string | number | undefined,
): boolean {
  if (previousIdentity === nextIdentity) {
    return false;
  }

  // First id assignment after create — same template session.
  const isCreateSessionIdentity = (identity: string | number | undefined) =>
    identity === undefined
    || identity === 'create'
    || (typeof identity === 'string' && identity.startsWith('create:'));

  if (isCreateSessionIdentity(previousIdentity) && typeof nextIdentity === 'number') {
    return false;
  }

  return previousIdentity !== undefined || nextIdentity !== undefined;
}
