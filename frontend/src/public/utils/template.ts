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
    viewers: template.viewers || [],
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

export const mapTemplateRequest = (template: ITemplate): ITemplateRequest => {
  const { tasks } = template;

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
    ...template,
    name: template.name || DEFAULT_TEMPLATE_NAME,
    tasks: normilizedTasks,
    publicSuccessUrl: template.publicSuccessUrl || null,
    viewers: template.viewers ?? [],
  };
};
