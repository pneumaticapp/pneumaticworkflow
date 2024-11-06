import {
  EDashboardActivityAction,
  EWorkflowLogEvent,
  ECommentType,
  IWorkflowDetailsKickoff,
  ITaskCommentAttachmentRequest,
} from '../types/workflow';
import {
  ITemplateTask,
  IKickoff,
  IExtraField,
} from '../types/template';
import { isArrayWithItems, deepCopy } from './helpers';
import { ExtraFieldsHelper } from '../components/TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { TUploadedFile } from './uploadFiles';

export const MAP_COMMENT_LOG: {[key: number]: EWorkflowLogEvent} = {
  [EDashboardActivityAction.Reverted]: EWorkflowLogEvent.TaskRevert,
  [EDashboardActivityAction.Comment]: EWorkflowLogEvent.TaskComment,
};

export const COMMENT_FIELD_PLACEHOLDER: {[key in ECommentType]: string} = {
  [ECommentType.Comment]: 'Your comment...',
  [ECommentType.Reverted]: 'State the reason for return',
  [ECommentType.Finish]: 'State the reason for workflow completion',
};

export const moveTask = (a: number, b: number, arr: ITemplateTask[]): ITemplateTask[] => {
  if (!isArrayWithItems(arr)) {
    return [];
  }

  if (!Number.isFinite(a) && !Number.isFinite(b)) {
    return arr;
  }

  if (!arr[b]) {
    return arr;
  }

  const copy = deepCopy(arr);
  const tmp = copy[a].number;
  copy[a].number = copy[b].number;
  copy[b].number = tmp;

  return copy;
};

export const moveWorkflowField = (a: number, b: number, arr: IExtraField[]) => {

  if (!Number.isFinite(a) && !Number.isFinite(b)) {
    return arr;
  }

  if (!arr[b]) {
    return arr;
  }

  const copy = deepCopy(arr);
  const tmp = copy[a].order;
  copy[a].order = copy[b].order;
  copy[b].order = tmp;

  return copy;
};

export const getEditKickoff = (kickoff: IWorkflowDetailsKickoff): IKickoff => {
  const kickoffFields = new ExtraFieldsHelper(kickoff.output).getFieldsWithValues();
  const kickoffDescritpiton = kickoff.description || '';

  return { description: kickoffDescritpiton, fields: kickoffFields };
};

export const getNormalizeFieldsOrders = (fields?: IExtraField[]): IExtraField[] => {
  if (!fields) {
    return [];
  }

  return fields.map((field, index) => ({ ...field, order: fields.length - index - 1 }));
};

export const mapFilesToRequest = (files?: TUploadedFile[]) => {
  if (!files || !isArrayWithItems(files)) {
    return [];
  }

  return files.map(file => ({ id: file.id } as ITaskCommentAttachmentRequest));
};
