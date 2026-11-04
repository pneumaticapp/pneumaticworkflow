import { randomBytes } from 'node:crypto';

import { ConnectorError } from '../core/errors.js';
import { isRecord, records } from '../core/json.js';

export type RawTask = Record<string, unknown>;

// The simple start rules the connector can read and rewire; anything else is treated as 'complex' and left alone.
export type StartRule = { after: 'kickoff' } | { after: 'step'; apiName: string };

export const newTaskApiName = () => `task-${randomBytes(4).toString('hex')}`;

export function sortedTasks(template: Record<string, unknown>): RawTask[] {
  return records(template.tasks).sort((a, b) => Number(a.number) - Number(b.number));
}

export function renumber(tasks: RawTask[]): RawTask[] {
  tasks.forEach((task, index) => {
    task.number = index + 1;
  });
  return tasks;
}

export function startRuleAfter(previous: RawTask | undefined): StartRule {
  return previous ? { after: 'step', apiName: String(previous.api_name) } : { after: 'kickoff' };
}

// Without start_task conditions Pneumatic starts every step in parallel; chain them to run one after another.
export function startCondition(rule: StartRule) {
  return {
    action: 'start_task',
    order: 1,
    rules: [
      {
        predicates: [
          rule.after === 'step'
            ? { field_type: 'task', operator: 'completed', field: rule.apiName, value: null }
            : { field_type: 'kickoff', operator: 'completed', field: null, value: null },
        ],
      },
    ],
  };
}

const isStartCondition = (condition: unknown) => isRecord(condition) && condition.action === 'start_task';

const conditionsOf = (task: RawTask): unknown[] => (Array.isArray(task.conditions) ? task.conditions : []);

export const usesStartRules = (tasks: RawTask[]) => tasks.some((task) => conditionsOf(task).some(isStartCondition));

// Skip conditions may sit beside the start rule and are not part of it.
export function readStartRule(task: RawTask): StartRule | 'none' | 'complex' {
  const starts = conditionsOf(task).filter(isStartCondition);
  if (!starts.length) {
    return 'none';
  }
  const [condition] = starts;
  const rules = isRecord(condition) && Array.isArray(condition.rules) ? condition.rules : [];
  const predicates = isRecord(rules[0]) && Array.isArray(rules[0].predicates) ? rules[0].predicates : [];
  const [predicate] = predicates;
  if (starts.length !== 1 || rules.length !== 1 || predicates.length !== 1 || !isRecord(predicate)) {
    return 'complex';
  }
  if (predicate.operator !== 'completed') {
    return 'complex';
  }
  if (predicate.field_type === 'kickoff') {
    return { after: 'kickoff' };
  }
  return predicate.field_type === 'task' && typeof predicate.field === 'string'
    ? { after: 'step', apiName: predicate.field }
    : 'complex';
}

// Whether the step starts exactly when `previous` completes (or, without `previous`, right after the kickoff).
export function startsRightAfter(task: RawTask, previous: RawTask | undefined): boolean {
  const rule = readStartRule(task);
  if (rule === 'none' || rule === 'complex') {
    return false;
  }
  const previousApiName = previous ? previous.api_name : null;
  return rule.after === 'kickoff' ? previousApiName === null : rule.apiName === previousApiName;
}

// Replaces only the start rule and keeps every other condition; null leaves the step without one (starts at once).
export function replaceStartRule(task: RawTask, rule: StartRule | null) {
  const others = conditionsOf(task).filter((condition) => !isStartCondition(condition));
  task.conditions = rule === null ? others : [...others, startCondition(rule)];
}

// Overwrites all conditions so the steps run one after another in the given order.
export function chainInOrder(tasks: RawTask[]) {
  tasks.forEach((task, index) => {
    task.api_name ??= newTaskApiName();
    task.conditions = [startCondition(startRuleAfter(tasks[index - 1]))];
  });
}

// Steps that waited for the removed step now start the way the removed step did.
export function rewireSuccessors(tasks: RawTask[], removed: RawTask) {
  const inherited = readStartRule(removed);
  for (const task of tasks) {
    if (task === removed || !startsRightAfter(task, removed)) {
      continue;
    }
    if (inherited === 'complex') {
      throw new ConnectorError(
        'invalid_arguments',
        `"${String(task.name)}" waits for this step, which has a complex start condition; change it first`,
      );
    }
    replaceStartRule(task, inherited === 'none' ? null : inherited);
  }
}

export function fieldApiNamesOf(task: RawTask): string[] {
  return [task.fields, ...records(task.fieldsets).map((set) => set.fields)]
    .flatMap(records)
    .map((item) => String(item.api_name));
}

// After a removal nothing may still name the removed step or field: Pneumatic does not validate drafts, so a stale
// reference would only surface when the template is activated.
export function assertUnreferenced(template: Record<string, unknown>, apiNames: string[], what: string) {
  const places = [...sortedTasks(template), { ...template, tasks: [], name: 'the kickoff form or template settings' }];
  // parents and ancestors are read-only lists Pneumatic recomputes, so they are not references.
  const serialize = (place: unknown) =>
    JSON.stringify(place, (key, value: unknown) => (key === 'parents' || key === 'ancestors' ? undefined : value));
  const problems = apiNames.flatMap((name) =>
    places
      .filter((place) => {
        const text = serialize(place);
        return (
          text.includes(JSON.stringify(name)) ||
          new RegExp(`\\{\\{\\s*${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\}\\}`).test(text)
        );
      })
      .map((place) => `"${String(place.name)}" still refers to ${what} ${name}`),
  );
  if (problems.length) {
    throw new ConnectorError('invalid_arguments', `${problems.join('; ')}. Change those references first.`);
  }
}
