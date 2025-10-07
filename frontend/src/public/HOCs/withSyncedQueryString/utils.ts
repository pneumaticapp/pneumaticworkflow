import { Dispatch } from 'redux';
import { getQueryStringParams } from '../../utils/history';
import { loadTemplateFieldsFromLocalStorage } from '../../redux/actions';
import { setWorkflowsFilterSelectedFields } from '../../redux/workflows/actions';
import { IAuthUser } from '../../types/redux';

export const updateFieldsFromUrl = (locationSearch: string, dispatch: Dispatch) => {
  const currentParams = getQueryStringParams(locationSearch);
  const currentTemplateId = currentParams.templates ? +currentParams.templates.split(',')[0] : null;

  if (currentTemplateId) {
    if (currentParams.fields) {
      const selectedFields = currentParams.fields.split(',');
      dispatch(
        setWorkflowsFilterSelectedFields({
          templateId: currentTemplateId,
          selectedFields,
        }),
      );
    } else {
      dispatch(
        setWorkflowsFilterSelectedFields({
          templateId: currentTemplateId,
          selectedFields: [],
        }),
      );
    }
  }
};

export const loadFieldsFromLocalStorage = (authUser: IAuthUser | null, dispatch: Dispatch) => {
  const userId = authUser?.id;

  if (!userId) {
    return;
  }

  const allTemplateFields: { [templateId: number]: string[] } = {};
  const keys = Object.keys(localStorage);

  keys.forEach((key) => {
    if (key.startsWith(`workflows_fields_user_${userId}_template_`)) {
      const savedFields = localStorage.getItem(key);
      if (savedFields) {
        try {
          const fields = JSON.parse(savedFields);
          const templateId = parseInt(key.split('_').pop() || '0', 10);
          allTemplateFields[templateId] = fields;
        } catch (error) {
          console.error('Error parsing fields from localStorage:', error);
        }
      }
    }
  });

  if (Object.keys(allTemplateFields).length > 0) {
    dispatch(loadTemplateFieldsFromLocalStorage(allTemplateFields));
  }
};
