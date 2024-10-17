import { IKickoff} from '../types/template';
import { isArrayWithItems } from './helpers';
import { IRunWorkflow } from '../components/WorkflowEditPopup/types';
import { ExtraFieldsHelper } from '../components/TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { IStartWorkflowPayload } from '../redux/actions';

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
  options: OptionsMapRequestBody = {}): string {

  return JSON.stringify(
    mapToSnakeCase(
      requestBody as { [key: string]: T },
      options.ignorePropertyMapToSnakeCase
    ),
    null,
    mode === 'prettify' ? 2 : undefined
  );
}

export const mapWorkflowToRunProcess = (workflow: IRunWorkflow) => {
  const { id, name, kickoff, isUrgent, dueDate, ancestorTaskId } = workflow;

  const mapWorkflow: IStartWorkflowPayload = {
    id,
    name,
    kickoff: getNormalizedKickoff(kickoff),
    isUrgent,
    dueDate,
  };

  if (ancestorTaskId) {
    mapWorkflow.ancestorTaskId = ancestorTaskId;
  }

  return mapWorkflow;
};

export const getNormalizedKickoff = (kickoff: IKickoff): { [key: string]: string } => {
  const mappedKickoffFields = new ExtraFieldsHelper(kickoff.fields).normalizeFieldsValues();
  const mappedKickoff = isArrayWithItems(mappedKickoffFields) ? Object.assign({}, ...mappedKickoffFields) : null;
  return mappedKickoff;
};
