import { IExtraField, IRuntimeKickoffClient } from '../types/template';
import { isArrayWithItems } from './helpers';
import { IRunWorkflow } from '../components/WorkflowEditPopup/types';
import { ExtraFieldsHelper } from '../components/TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { normalizeCheckboxValue } from './fields';
import {
  getEndOfDayTsp,
  toDateString,
  toTspDate,
  toISOStringFromTsp,
  formatDateToISOInWorkflow,
  formatDateToISOInTask,
} from './dateTime';
import {
  IWorkflow,
  IWorkflowDetails,
  IWorkflowDetailsKickoff,
  IWorkflowLogItem,
  TWorkflowDetailsKickoffResponse,
  TWorkflowDetailsResponse,
  WorkflowWithDateFields,
  WorkflowWithTsp,
  WorkflowWithTspFields,
} from '../types/workflow';
import { IHighlightsItem, THighlightsItemResponse } from '../types/highlights';
import { TaskWithDateFields, TaskWithTspFields, TFormatTaskDates } from '../types/tasks';
import { getWorkflowAddComputedPropsToRedux } from '../components/Workflows/utils/getWorfkflowClientProperties';
import { IStartWorkflowPayload, TEditWorkflowPayload } from '../redux/workflows/types';
import { mapFieldsetTaskAPIToRuntime } from './mapFieldsetsAPIToClient';

interface OptionsMapRequestBody {
  ignorePropertyMapToSnakeCase?: string[];
}

export const isObject = (o: object) => {
  return o === Object(o) && !Array.isArray(o) && typeof o !== 'function';
};

const toCamel = (s: string) =>
  s.replace(/([-_][a-z])/gi, (letter) => letter.toUpperCase().replace('-', '').replace('_', ''));

export const mapToCamelCase = (o: object): object => {
  if (isObject(o)) {
    const n: { [key: string]: any } = {};

    Object.keys(o).forEach((k: keyof typeof o) => {
      n[toCamel(k)] = mapToCamelCase(o[k]);
    });

    return n;
  }

  if (Array.isArray(o)) {
    return o.map((i) => {
      return mapToCamelCase(i);
    });
  }

  return o;
};

export const mapToSnakeCase = (o: object, ignoreProperty: string[] = []): object => {
  if (isObject(o)) {
    const n: { [key: string]: any } = {};

    Object.keys(o).forEach((k: keyof typeof o) => {
      n[camelToSnake(k)] = !ignoreProperty.indexOf(k) ? o[k] : mapToSnakeCase(o[k]);
    });

    return n;
  }

  if (Array.isArray(o)) {
    return o.map((i) => {
      return mapToSnakeCase(i);
    });
  }

  return o;
};

function camelToSnake(str: string) {
  return str.replace(/[\w]([A-Z])/g, (match) => `${match[0]}_${match[1]}`).toLowerCase();
}

export function mapRequestBody<T>(
  requestBody: object,
  mode: 'prettify' | 'default' = 'default',
  options: OptionsMapRequestBody = {},
): string {
  return JSON.stringify(
    mapToSnakeCase(requestBody as { [key: string]: T }, options.ignorePropertyMapToSnakeCase),
    null,
    mode === 'prettify' ? 2 : undefined,
  );
}

export const mapOutputToCompleteTask = (output: IExtraField[]): IExtraField[] => {
  if (output.length === 0) {
    return output;
  }
  return output.map((item) => {
    if (item.type === 'date' && typeof item.value === 'string') {
      return {
        ...item,
        value: getEndOfDayTsp(item.value),
      };
    }
    if (item.type === 'number') {
      return {
        ...item,
        value: String(item.value).replace(',', '.'),
      };
    }
    if (item.type === 'checkbox') {
      return { ...item, value: normalizeCheckboxValue(item.value) };
    }
    return item;
  });
};

export const mapWorkflowToRunProcess = (workflow: IRunWorkflow) => {
  const { id, name, kickoff, isUrgent, dueDate, ancestorTaskId } = workflow;

  const mapWorkflow: IStartWorkflowPayload = {
    id,
    name,
    kickoff: getNormalizedKickoff(kickoff),
    isUrgent,
    dueDateTsp: toTspDate(dueDate),
  };

  if (ancestorTaskId) {
    mapWorkflow.ancestorTaskId = ancestorTaskId;
  }

  return mapWorkflow;
};

export const formatDueDateToEditWorkflow = (payload: TEditWorkflowPayload): TEditWorkflowPayload => {
  if ('dueDate' in payload) {
    const { dueDate, ...rest } = payload;
    return {
      ...rest,
      dueDateTsp: toTspDate(payload.dueDate),
    };
  }

  if ('kickoff' in payload) {
    if (!payload.kickoff?.fields?.length) return payload;
    return {
      ...payload,
      kickoff: {
        ...payload.kickoff,
        fields: mapEndOfDayTsp(payload.kickoff.fields),
      },
    };
  }

  return payload;
};

export const mapEndOfDayTsp = (fields: IExtraField[]): IExtraField[] => {
  return fields.map((item: any) => ({
    ...item,
    value: item.type === 'date' && typeof item.value === 'string' ? getEndOfDayTsp(item.value) : item.value,
  }));
};

export const getNormalizedKickoff = (kickoff: Pick<IRuntimeKickoffClient, 'fields'>): { [key: string]: string } => {
  const mappedKickoffFields = new ExtraFieldsHelper(kickoff.fields).normalizeFieldsValues();
  const mappedKickoff = isArrayWithItems(mappedKickoffFields) ? Object.assign({}, ...mappedKickoffFields) : null;
  return mappedKickoff;
};

export const getNormalizeOutputUsersToEmails = (
  outputs: IExtraField[],
  setUsers: Map<number, string>,
): IExtraField[] => {
  return outputs.map((output) => {
    const { value, type, userId } = output;
    if (type === 'user' && userId !== null) {
      return { ...output, value: setUsers.get(userId as number) || value };
    }
    return output;
  });
};

export const mapTasksToISOStringToRedux = <T extends TaskWithTspFields>(
  tasks: T[],
): (Omit<T, keyof TaskWithTspFields> & TaskWithDateFields)[] => {
  return tasks.map((task) => {
    return formatDateToISOInTask(task);
  });
};

export const mapWorkflowsToISOStringToRedux = <T extends WorkflowWithTspFields>(
  workflows: T[],
): (Omit<T, keyof WorkflowWithTspFields> & WorkflowWithDateFields)[] => {
  return workflows.map((workflow) => {
    return formatDateToISOInWorkflow(workflow);
  });
};

export const mapWorkflowsForSetHighlights = (
  resultsFromGetHighlights: Array<THighlightsItemResponse>,
  timezone: string,
): IHighlightsItem[] => {
  return resultsFromGetHighlights.map((result) => ({
    ...result,
    workflow: {
      ...result.workflow,
      kickoff: mapBackendKickoffToRedux(result.workflow.kickoff, timezone),
    },
    task: result.task ? formatTaskDatesForRedux(result.task, timezone) : null,
  }));
};

export const mapBackendKickoffToRuntime = (
  kickoff: TWorkflowDetailsKickoffResponse | null,
): IWorkflowDetailsKickoff | null => {
  if (!kickoff) return null;

  return {
    ...kickoff,
    fieldsets: mapFieldsetTaskAPIToRuntime(kickoff.fieldsets),
  };
};

export const mapBackendKickoffToRedux = (
  kickoff: TWorkflowDetailsKickoffResponse | null,
  timezone: string,
): IWorkflowDetailsKickoff | null => {
  const runtimeKickoff = mapBackendKickoffToRuntime(kickoff);
  if (!runtimeKickoff) return null;

  return {
    ...runtimeKickoff,
    output: mapTspToString(runtimeKickoff.output, timezone),
    fieldsets: runtimeKickoff.fieldsets.map((fieldset) => ({
      ...fieldset,
      fields: mapTspToString(fieldset.fields, timezone),
    })),
  };
};

export const mapBackendWorkflowToRedux = (
  workflow: TWorkflowDetailsResponse,
  timezone: string,
): WorkflowWithTsp<IWorkflowDetails> => {
  const kickoff = mapBackendKickoffToRedux(workflow.kickoff, timezone);
  if (!kickoff) {
    throw new Error('kickoff is required in workflow details');
  }

  return {
    ...workflow,
    kickoff,
  };
};

export const mapBackandworkflowLogToRedux = (workflowLog: IWorkflowLogItem[], timezone: string): IWorkflowLogItem[] => {
  return workflowLog.map((item) => mapBackendNewEventToRedux(item, timezone));
};

export const mapTspToString = (output: IExtraField[], timezone: string): IExtraField[] => {
  return output.map((item) => {
    if (item.type !== 'date' || item.value == null || item.value === '') {
      return item;
    }

    if (typeof item.value !== 'string' && typeof item.value !== 'number') {
      return item;
    }

    return {
      ...item,
      value: toDateString(item.value, timezone),
    };
  });
};

export const formatTaskDatesForRedux = <T extends TFormatTaskDates>(
  task: T,
  timezone: string,
): Omit<T, 'dueDateTsp' | 'subWorkflows' | 'dateStartedTsp' | 'dateCompletedTsp'> & {
  dueDate: string | null;
  subWorkflows?: IWorkflow[] | null;
  dateStarted?: string;
  dateCompleted?: string;
} => {
  const formattedTask = {
    ...task,
    dueDate: task.dueDateTsp ? toISOStringFromTsp(task.dueDateTsp) : null,
    ...(task.dateStartedTsp && { dateStarted: toISOStringFromTsp(task.dateStartedTsp) }),
    ...(task.dateCompletedTsp && { dateCompleted: toISOStringFromTsp(task.dateCompletedTsp) }),
    ...(task.output && { output: mapTspToString(task.output, timezone) }),
    ...(task.fieldsets?.length && {
      fieldsets: task.fieldsets.map((fieldset) => ({
        ...fieldset,
        fields: mapTspToString(fieldset.fields, timezone),
      })),
    }),
    ...(task.subWorkflows && {
      subWorkflows: mapWorkflowsAddComputedPropsToRedux(mapWorkflowsToISOStringToRedux(task.subWorkflows)),
    }),
  };
  delete formattedTask.dueDateTsp;
  delete formattedTask.dateStartedTsp;
  delete formattedTask.dateCompletedTsp;
  return formattedTask;
};

export const mapBackendNewEventToRedux = (event: IWorkflowLogItem, timezone: string): IWorkflowLogItem => {
  if (!event.task) return event;
  return {
    ...event,
    task: formatTaskDatesForRedux(event.task, timezone),
  };
};

export const mapWorkflowsAddComputedPropsToRedux = (items: IWorkflow[]) => {
  return items.map((workflow) => {
    return getWorkflowAddComputedPropsToRedux(workflow);
  });
};
