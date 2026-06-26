import { IExtraField, IKickoffClient } from '../types/template';
import { isArrayWithItems } from './helpers';
import { IRunWorkflow } from '../components/WorkflowEditPopup/types';
import { ExtraFieldsHelper } from '../components/TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
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
  IWorkflowDetailsKickoff,
  IWorkflowLogItem,
  WorkflowWithDateFields,
  WorkflowWithTspFields,
} from '../types/workflow';
import { IHighlightsItem } from '../types/highlights';
import { TaskWithDateFields, TaskWithTspFields, TFormatTaskDates } from '../types/tasks';
import { getWorkflowAddComputedPropsToRedux } from '../components/Workflows/utils/getWorfkflowClientProperties';
import { IStartWorkflowPayload, TEditWorkflowPayload } from '../redux/workflows/types';

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
      let checkboxValue: string[];
      if (Array.isArray(item.value)) {
        checkboxValue = item.value;
      } else if (item.value) {
        checkboxValue = (item.value as string).split(', ');
      } else {
        checkboxValue = [];
      }

      return { ...item, value: checkboxValue };
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

export const getNormalizedKickoff = (kickoff: IKickoffClient): { [key: string]: string } => {
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

export const mapWorkflowsForSetHighlights = (resultsFromGetHighlights: Array<IHighlightsItem>, timezone: string) => {
  return resultsFromGetHighlights.map((result) => ({
    ...result,
    workflow: mapBackendWorkflowToRedux(result.workflow, timezone),
    task: result.task ? formatTaskDatesForRedux(result.task, timezone) : null,
  }));
};

export const mapBackendWorkflowToRedux = <Workflow extends { kickoff: IWorkflowDetailsKickoff | null }>(
  workflow: Workflow,
  timezone: string,
): Workflow => {
  if (!workflow.kickoff) return workflow;

  const hasOutput = workflow.kickoff.output?.length;
  const hasFieldsets = workflow.kickoff.fieldsets?.length;

  if (!hasOutput && !hasFieldsets) return workflow;

  return {
    ...workflow,
    kickoff: {
      ...workflow.kickoff,
      ...(hasOutput && { output: mapTspToString(workflow.kickoff.output, timezone) }),
      ...(hasFieldsets && {
        fieldsets: workflow.kickoff.fieldsets!.map((fieldset) => ({
          ...fieldset,
          fields: mapTspToString(fieldset.fields, timezone),
        })),
      }),
    },
  };
};

export const mapBackandworkflowLogToRedux = (workflowLog: IWorkflowLogItem[], timezone: string): IWorkflowLogItem[] => {
  return workflowLog.map((item) => mapBackendNewEventToRedux(item, timezone));
};

export const mapTspToString = (output: IExtraField[], timezone: string): IExtraField[] => {
  return output.map((item) => ({
    ...item,
    value: item.type === 'date' && typeof item.value === 'string' ? toDateString(item.value, timezone) : item.value,
  }));
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
