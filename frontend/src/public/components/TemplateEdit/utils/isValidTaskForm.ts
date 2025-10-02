/* eslint-disable */
/* prettier-ignore */
import { ITemplateTask } from '../../../types/template';
import { areExtraFieldsValid } from './areExtraFieldsValid';

export function isValidTaskForm(task: ITemplateTask) {
  return areExtraFieldsValid(task.fields);
}
