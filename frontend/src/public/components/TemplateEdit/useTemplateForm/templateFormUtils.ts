import { ITemplate, ITemplateTask } from '../../../types/template';

export function setNestedFieldValue(obj: ITemplate, path: string, value: unknown): ITemplate {
  const taskPathMatch = path.match(/^tasks\.(\d+)(?:\.(.+))?$/);

  if (taskPathMatch) {
    const index = Number(taskPathMatch[1]);
    const taskField = taskPathMatch[2];
    const tasks = [...obj.tasks];

    if (!taskField) {
      tasks[index] = value as ITemplateTask;
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
  incomingTasks: ITemplateTask[],
  preservedTasks: ITemplateTask[],
  baselineTasks: ITemplateTask[],
): ITemplateTask[] {
  const incomingByUuid = new Map(incomingTasks.map((task) => [task.uuid, task]));
  const baselineUuids = new Set(baselineTasks.map((task) => task.uuid));

  const mergedFromPreserved = preservedTasks.map((preserved) => {
    const incoming = incomingByUuid.get(preserved.uuid);

    if (!incoming || preserved === incoming) {
      return preserved;
    }

    const onlyAncestorsDiffer = (Object.keys(preserved) as (keyof ITemplateTask)[]).every(
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
  const preservedOrderNumber = (task: ITemplateTask) =>
    incomingByUuid.get(task.uuid)?.number ?? task.number;

  const insertState = { serverIndex: 0 };

  const interleaved = mergedFromPreserved.reduce<ITemplateTask[]>((result, preserved) => {
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
  initialValues: ITemplate,
  pendingEdits: Partial<ITemplate>,
  baselineValues: ITemplate,
): ITemplate {
  if (Object.keys(pendingEdits).length === 0) {
    return initialValues;
  }

  let mergedValues: ITemplate = { ...initialValues, ...pendingEdits };

  if (pendingEdits.tasks && initialValues.tasks) {
    mergedValues = {
      ...mergedValues,
      tasks: mergePreservedTasks(initialValues.tasks, pendingEdits.tasks, baselineValues.tasks),
    };
  }

  return mergedValues;
}

export function overlayPendingEdits(
  formikValues: ITemplate,
  pendingEdits: Partial<ITemplate>,
  baselineValues: ITemplate,
): ITemplate {
  if (Object.keys(pendingEdits).length === 0) {
    return formikValues;
  }

  return applyPendingEdits(formikValues, pendingEdits, baselineValues);
}

export function getChangedFields(previous: ITemplate, next: ITemplate): Partial<ITemplate> {
  const changedFields: Partial<ITemplate> = {};

  (Object.keys(next) as (keyof ITemplate)[]).forEach((key) => {
    if (previous[key] !== next[key]) {
      (changedFields[key] as ITemplate[keyof ITemplate]) = next[key];
    }
  });

  return changedFields;
}

export function getUnconsumedPendingEdits(
  consumed: Partial<ITemplate>,
  current: Partial<ITemplate>,
): Partial<ITemplate> {
  const remainder: Partial<ITemplate> = {};

  (Object.keys(current) as (keyof ITemplate)[]).forEach((key) => {
    if (current[key] !== consumed[key]) {
      (remainder[key] as ITemplate[keyof ITemplate]) = current[key];
    }
  });

  return remainder;
}

export function resolveTemplateIdentity(
  initialValues: ITemplate,
  templateIdentityKey?: string | number,
): string | number | undefined {
  if (templateIdentityKey !== undefined) {
    return templateIdentityKey;
  }

  return initialValues.id;
}

export function hasTemplateIdentityChanged(
  previousIdentity: string | number | undefined,
  nextIdentity: string | number | undefined,
): boolean {
  if (previousIdentity === nextIdentity) {
    return false;
  }

  // First id assignment after create — same template session.
  if (previousIdentity === undefined && typeof nextIdentity === 'number') {
    return false;
  }

  return previousIdentity !== undefined || nextIdentity !== undefined;
}
