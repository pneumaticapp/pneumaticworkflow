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
} from '../types/template';
import { getUrlParams } from './getUrlParams';
import { DEFAULT_TEMPLATE_NAME } from '../components/TemplateEdit/constants';

import { getNormalizeFieldsOrders } from './workflows';
import { createTaskApiName, createUUID } from './createId';
import { isArrayWithItems, omit } from './helpers';
import { getEmptyConditions } from '../components/TemplateEdit/TaskForm/Conditions/utils/getEmptyConditions';
import { normalizeConditiosForFrontend } from './conditions/normalizeConditiosForFrontend';
import { normalizeConditionForBackend } from './conditions/normalizeConditionForBackend';
import { isEmptyDuration } from './dateTime';
import { TUserListItem } from '../types/user';
import { getNotDeletedUsers } from './users';
import { normalizeDueDateForFrontend } from './dueDate/normalizeDueDateForFrontend';
import { normalizeDueDateForBackend } from './dueDate/normalizeDueDateForBackend';

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
): ITemplate => {
  const normalizedKickoff = template.kickoff || getEmptyKickoff();
  const normalizedTasks = [...template.tasks]
    .sort((a, b) => a.number - b.number)
    .map((task, index, tasks) => getNormalizedTask(task, isSubscribed, tasks[index - 1]));

  const normalizedTemplateOwners = getNormalizedTemplateOwners(template.templateOwners, isSubscribed, users);

  return {
    ...template,
    kickoff: normalizedKickoff,
    tasks: normalizedTasks,
    templateOwners: normalizedTemplateOwners,
  };
};

export const getNormalizedTemplateOwners = (
  initialTemplateOwners: ITemplate['templateOwners'],
  isSubscribed: boolean,
  users: TUserListItem[],
) => {
  if (isSubscribed) {
    return initialTemplateOwners;
  }

  return getNotDeletedUsers(users).map((user) => user.id);
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
  };
};
