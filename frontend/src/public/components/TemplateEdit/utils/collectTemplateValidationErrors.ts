import type { IntlShape } from 'react-intl';

import type { IFieldsetBindingClient } from '../../../types/fieldset';
import type { IExtraField, ITemplateClient } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { validateFieldsetTitle } from '../../../utils/validators';
import { createTemplateValidationError } from '../../../redux/templateValidation/getValidationErrorTarget';
import type { ITemplateValidationError } from '../../../redux/templateValidation/types';
import { getConditionRuleErrorId } from '../TaskForm/Conditions/utils/conditionsValidators';
import { ETaskFormParts } from '../types';
import { getExtraFieldErrorId } from './getExtraFieldErrorId';

export function collectTemplateValidationErrors(
  template: ITemplateClient,
  formatMessage: IntlShape['formatMessage'],
): ITemplateValidationError[] {
  const errors: ITemplateValidationError[] = [];

  const addError = (apiName: string, messageId: string, taskSection: ETaskFormParts | null = null) => {
    const error = createTemplateValidationError(template, apiName, formatMessage({ id: messageId }), taskSection);
    if (error) errors.push(error);
  };

  const checkOutputs = (fields: IExtraField[], fieldsets: IFieldsetBindingClient[] = []) => {
    fields.forEach((field) => {
      const errorId = getExtraFieldErrorId(field);
      if (errorId) addError(field.apiName, errorId);
    });
    fieldsets.forEach((fieldset) => {
      const errorId = validateFieldsetTitle(fieldset.title);
      if (errorId) addError(fieldset.apiNameBinding, errorId);
    });
  };

  checkOutputs(template.kickoff.fields, template.kickoff.fieldsets);

  [...template.tasks]
    .sort((first, second) => first.number - second.number)
    .forEach((task) => {
      if (!isArrayWithItems(task.rawPerformers)) {
        addError(task.apiName, 'validation.task-performers-empty', ETaskFormParts.AssignPerformers);
      }
      checkOutputs(task.fields, task.fieldsets);
      task.conditions.forEach(({ rules }) =>
        rules.forEach((rule) => {
          const errorId = getConditionRuleErrorId(rule);
          if (errorId) addError(rule.predicateApiName, errorId);
        }),
      );
    });

  return errors;
}
