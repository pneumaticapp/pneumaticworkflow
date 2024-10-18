/* eslint-disable */
/* prettier-ignore */
import { IntlShape } from 'react-intl';
import { EExtraFieldType, IExtraField } from '../../../../types/template';
import { createFieldApiName } from '../../../../utils/createId';
import { getEmptySelection } from './getEmptySelection';

export const getEmptyField = (type: EExtraFieldType, formatMessage: IntlShape['formatMessage'], order = 0) => {
  const EMPTY_FIELD = {
    description: '',
    isRequired: false,
    name: 'Field name',
    order,
    type,
    apiName: createFieldApiName(),
  };

  const emptyFieldsMap: { [key in EExtraFieldType]: IExtraField } = {
    [EExtraFieldType.Text]: { ...EMPTY_FIELD, name: formatMessage({ id: 'template.kick-off-form-large-text-field-tooltip-title' }) },
    [EExtraFieldType.String]: { ...EMPTY_FIELD, name: formatMessage({ id: 'template.kick-off-form-small-text-field-tooltip-title' }) },
    [EExtraFieldType.Url]: {
      ...EMPTY_FIELD,
      name: formatMessage({ id: 'template.kick-off-form-url-field-tooltip-title' }),
    },
    [EExtraFieldType.Date]: { ...EMPTY_FIELD, name: formatMessage({ id: 'template.kick-off-form-date-field-tooltip-title' }) },
    [EExtraFieldType.Checkbox]: {
      ...EMPTY_FIELD,
      selections: [getEmptySelection()],
      name: formatMessage({ id: 'template.kick-off-form-checkbox-field-tooltip-title' }),
    },
    [EExtraFieldType.Radio]: {
      ...EMPTY_FIELD,
      selections: [getEmptySelection()],
      name: formatMessage({ id: 'template.kick-off-form-radio-field-tooltip-title' }),
    },
    [EExtraFieldType.Creatable]: {
      ...EMPTY_FIELD,
      selections: [getEmptySelection()],
      name: formatMessage({ id: 'template.kick-off-form-creatable-field-tooltip-title' }),
    },
    [EExtraFieldType.User]: {
      ...EMPTY_FIELD,
      name: formatMessage({ id: 'template.kick-off-form-user-field-tooltip-title' }),
      isRequired: true,
    },
    [EExtraFieldType.File]: { ...EMPTY_FIELD, name: formatMessage({ id: 'template.kick-off-form-attachment-field-tooltip-title' }) },
  };

  const emptyField = emptyFieldsMap[type];

  return emptyField;
};
