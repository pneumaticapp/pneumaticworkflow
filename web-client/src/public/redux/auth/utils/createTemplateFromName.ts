import { call } from 'redux-saga/effects';
import { getTemplateName, resetTemplateName } from '../../../views/user/Register/utils/templateName';
import { createTemplateByName } from '../../../api/createTemplateByName';
import { ITemplate } from '../../../types/template';

export function* createTemplateFromName() {
  try {
    const templateName = getTemplateName();

    if (templateName) {
      const template: ITemplate = yield call(createTemplateByName, { name: templateName });
      resetTemplateName();
      return template?.id;
    }

    return null;
  } catch (error) {
    return null;
  }
}
