import { ITemplateTaskClient } from '../../../types/template';
import { areExtraFieldsValid } from './areExtraFieldsValid';
import { areFieldsetsValid } from './areFieldsetsValid';

export function isValidTaskForm(task: ITemplateTaskClient) {
  return areExtraFieldsValid(task.fields) && areFieldsetsValid(task.fieldsets);
}
