/* eslint-disable */
/* prettier-ignore */
import {
  ITemplate,
  ITemplateRequest,
  ITemplateTask,
  IKickoff,
  ITemplateTaskRequest,
  ITemplateResponse,
  ITemplateTaskResponse,
  ITemplateTaskPerformer,
  ETemplateOwnerType,
  ETemplateOwnerRole,
  ITemplateOwner,
} from '../types/template';
import { getUrlParams } from './getUrlParams';
import { DEFAULT_TEMPLATE_NAME } from '../components/TemplateEdit/constants';

import { getNormalizeFieldsOrders } from './workflows';
import { createOwnerApiName, createTaskApiName, createUUID } from './createId';
import { isArrayWithItems, omit } from './helpers';
import { getEmptyConditions } from '../components/TemplateEdit/TaskForm/Conditions/utils/getEmptyConditions';
import { normalizeConditiosForFrontend } from './conditions/normalizeConditiosForFrontend';
import { normalizeConditionForBackend } from './conditions/normalizeConditionForBackend';
import { isEmptyDuration } from './dateTime';
import { TUserListItem } from '../types/user';
import { getNotDeletedUsers } from './users';
import { normalizeDueDateForFrontend } from './dueDate/normalizeDueDateForFrontend';
import { normalizeDueDateForBackend } from './dueDate/normalizeDueDateForBackend';
import { ESubscriptionPlan } from '../types/account';

export function getTemplateIdFromUrl(url: string) {
  if (!url) {
    return null;
  }

  const { template } = getUrlParams(location.search);

  if (!template) {
    return null;
  }

  return Number(template) ? template : null;
}

export function getEmptyKickoff(): IKickoff {
  return {
    description: '',
    fields: [],
  };
}

export const getNormalizedTemplate = (
  template: ITemplateResponse,
  isSubscribed: boolean,
  users: TUserListItem[],
  billingPlan: ESubscriptionPlan,
): ITemplate => {
  const normalizedKickoff = template.kickoff || getEmptyKickoff();
  const normalizedTasks = [...template.tasks]
    .sort((a, b) => a.number - b.number)
    .map((task, index, tasks) => getNormalizedTask(task, isSubscribed, tasks[index - 1]));

  const performersCount = setPerformersCounts(normalizedTasks);
  const normalizedTemplateOwners =
    !isSubscribed && billingPlan !== ESubscriptionPlan.Free
      ? getNormalizedTemplateOwners(template.owners, isSubscribed, users)
      : template.owners;

  return {
    ...template,
    tasksCount: normalizedTasks.length,
    performersCount,
    kickoff: normalizedKickoff,
    tasks: normalizedTasks,
    owners: normalizedTemplateOwners,
  };
};

export const setPerformersCounts = <T extends { rawPerformers: ITemplateTaskPerformer[] }>(tasks: T[]): number => {
  const uniqueSourceIdSet = new Set();
  tasks.forEach((task) => {
    task.rawPerformers.forEach((item) => {
      if (item.type === 'user') {
        uniqueSourceIdSet.add(item.sourceId);
      }
    });
  });
  return uniqueSourceIdSet.size;
};

export const getNormalizedTemplateOwners = (
  initialTemplateOwners: ITemplate['owners'],
  isSubscribed: boolean,
  users: TUserListItem[],
) => {
  if (isSubscribed) {
    return initialTemplateOwners;
  }

  const mapOwnersNotDeletedUsers = getNotDeletedUsers(users).map((user) => {
    return {
      sourceId: String(user.id),
      apiName: createOwnerApiName(),
      type: ETemplateOwnerType.User,
      role: ETemplateOwnerRole.Owner,
    } as ITemplateOwner
  });

  return mapOwnersNotDeletedUsers;
};

export const getNormalizedTask = (
  task: ITemplateTaskResponse,
  isSubscribed: boolean,
  prevTask?: ITemplateTaskResponse,
): ITemplateTask => {
  const conditions = isArrayWithItems(task.conditions)
    ? normalizeConditiosForFrontend(task.conditions)
    : getEmptyConditions(isSubscribed);

  const rawDueDate = normalizeDueDateForFrontend(task);

  return {
    ...omit(task, ['dueIn']),
    apiName: task.apiName || createTaskApiName(),
    fields: getNormalizeFieldsOrders(task.fields),
    uuid: createUUID(),
    conditions,
    rawDueDate,
  };
};

export const cleanTemplateReferences = (template: ITemplate): ITemplate => {
  // System variables that the backend recognizes and skips during validation.
  // Must stay in sync with backend/src/processes/enums.py :: SystemVariable
  const TASK_SYSTEM_VARS = new Set(['workflow-starter']);
  const WF_NAME_SYSTEM_VARS = new Set(['date', 'template-name', 'workflow-id', 'workflow-starter']);

  const validApiNames = new Set<string>();

  template.kickoff?.fields?.forEach((f) => {
    if (f.apiName) validApiNames.add(f.apiName);
  });

  const removeInvalidReferences = (
    text: string | null | undefined,
    validApis: Set<string>,
    systemVars: Set<string>,
  ): string => {
    if (!text) return text || '';
    return text
      .replace(/\{\{\s*([\w-]+)\s*\}\}/g, (match, apiName) => {
        if (validApis.has(apiName) || systemVars.has(apiName)) {
          return match;
        }
        return '';
      })
      .trim();
  };

  const tasks = [...(template.tasks || [])].sort((a, b) => a.number - b.number);

  const cleanedTasks = tasks.map((task) => {
    const name = removeInvalidReferences(task.name, validApiNames, TASK_SYSTEM_VARS) || `Step ${task.number}`;
    const description = removeInvalidReferences(task.description, validApiNames, TASK_SYSTEM_VARS);

    const conditions = (task.conditions || []).map((condition) => {
      const rules = condition.rules.filter(
        (rule) => rule.field === undefined || rule.field === null || validApiNames.has(rule.field)
      );
      return { ...condition, rules };
    });

    const rawPerformers = (task.rawPerformers || []).filter((p) => {
      if (p.type === 'field') {
        return !!p.sourceId && validApiNames.has(p.sourceId);
      }
      return true;
    });

    let rawDueDate = task.rawDueDate;
    if (rawDueDate && rawDueDate.ruleTarget === 'field') {
      if (rawDueDate.sourceId && !validApiNames.has(rawDueDate.sourceId)) {
        rawDueDate = {
          ...rawDueDate,
          duration: null,
          durationMonths: null,
          sourceId: null,
          ruleTarget: 'task started',
        };
      }
    }

    (task.fields || []).forEach((f) => {
      if (f.apiName) validApiNames.add(f.apiName);
    });

    return {
      ...task,
      name,
      description,
      conditions,
      rawPerformers,
      rawDueDate,
    };
  });

  const validKickoffApiNames = new Set<string>();
  template.kickoff?.fields?.forEach((f) => {
    if (f.apiName) validKickoffApiNames.add(f.apiName);
  });

  return {
    ...template,
    wfNameTemplate: removeInvalidReferences(template.wfNameTemplate, validKickoffApiNames, WF_NAME_SYSTEM_VARS),
    tasks: cleanedTasks,
  };
};

export const mapTemplateRequest = (template: ITemplate): ITemplateRequest => {
  const cleanedTemplate = cleanTemplateReferences(template);
  const { tasks } = cleanedTemplate;

  const normilizedTasks: ITemplateTaskRequest[] = tasks?.map((task) => {
    const normalizeDuration = (duration: string | null) => {
      return isEmptyDuration(duration) ? null : duration;
    };

    return {
      ...omit(task, ['uuid']),
      delay: normalizeDuration(task.delay),
      conditions: normalizeConditionForBackend(task.conditions),
      rawDueDate: normalizeDueDateForBackend(task.rawDueDate),
    };
  });

  return {
    ...cleanedTemplate,
    name: cleanedTemplate.name || DEFAULT_TEMPLATE_NAME,
    tasks: normilizedTasks,
    publicSuccessUrl: cleanedTemplate.publicSuccessUrl || null,
  };
};
