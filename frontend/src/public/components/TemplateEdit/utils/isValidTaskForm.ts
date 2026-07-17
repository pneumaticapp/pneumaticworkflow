/* eslint-disable */
/* prettier-ignore */
import { ITemplateTaskClient } from '../../../types/template';
import { areExtraFieldsValid } from './areExtraFieldsValid';

export function isValidTaskForm(task: ITemplateTaskClient) {
  return areExtraFieldsValid(task.fields);
}
