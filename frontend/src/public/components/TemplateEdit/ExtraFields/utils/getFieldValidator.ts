/* eslint-disable indent */
import { EMPTY_RULE, IRule, isEmpty, isInvalidUrl, validateFieldCreator } from '../../../../utils/validators';
import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../../types/template';
import { isArrayWithItems } from '../../../../utils/helpers';
import { numberRegex } from '../../../../constants/defaultValues';

export const getFieldValidator = (field: IExtraField, mode: EExtraFieldMode) => {
  const shouldValidate = mode === EExtraFieldMode.ProcessRun;

  if (!shouldValidate) {
    return validateFieldCreator([EMPTY_RULE]);
  }

  const fieldValidateRulesMap: { [key in EExtraFieldType]: IRule[] } = {
    [EExtraFieldType.Number]: getNumberValidateRules(field),
    [EExtraFieldType.Text]: getTextValidateRules(field),
    [EExtraFieldType.String]: getStringValidateRules(field),
    [EExtraFieldType.Url]: getUrlValidateRules(field),
    [EExtraFieldType.Date]: getDateValidateRules(field),
    [EExtraFieldType.Checkbox]: getCheckboxValidateRules(field),
    [EExtraFieldType.Creatable]: getCreatableValidateRules(field),
    [EExtraFieldType.Radio]: getRadioValidateRules(field),
    [EExtraFieldType.File]: getAttachmentValidateRules(field),
    [EExtraFieldType.User]: getUserValidateRules(field),
  };

  const fieldValidateRules = fieldValidateRulesMap[field.type];

  return validateFieldCreator(fieldValidateRules);
};

export const hasFieldError = (field: IExtraField, mode: EExtraFieldMode) => {
  const { value } = field;

  const fieldValidator = getFieldValidator(field, mode);
  const validateMessage = fieldValidator(value);

  return Boolean(validateMessage);
};

export const KICKOFF_SIMPLE_FIELD_RULE: IRule = {
  message: 'validation.kickoff-form-field-empty',
  isInvalid: isEmpty,
};

function getTextValidateRules({ isRequired }: IExtraField) {
  return [isRequired ? KICKOFF_SIMPLE_FIELD_RULE : EMPTY_RULE];
}

function getAttachmentValidateRules({ isRequired }: IExtraField) {
  return [
    isRequired
      ? {
          message: 'validation.kickoff-form-field-empty',
          isInvalid: (value: number[]) => !isArrayWithItems(value),
        }
      : EMPTY_RULE,
  ];
}

function getStringValidateRules({ isRequired }: IExtraField) {
  return [isRequired ? KICKOFF_SIMPLE_FIELD_RULE : EMPTY_RULE];
}

function getNumberValidateRules({ isRequired }: IExtraField) {
  return [
    isRequired ? KICKOFF_SIMPLE_FIELD_RULE : EMPTY_RULE,
    {
      message: 'validation.number-invalid-format',
      isInvalid: (value: number) => {
        if (!value) {
          return false;
        }

        return !numberRegex.test(String(value));
      },
    },
  ];
}

function getUrlValidateRules({ isRequired }: IExtraField) {
  return [
    isRequired ? KICKOFF_SIMPLE_FIELD_RULE : EMPTY_RULE,
    {
      message: 'validation.kickoff-form-url-field-invalid',
      isInvalid: isInvalidUrl,
    },
  ];
}

function getDateValidateRules({ isRequired }: IExtraField) {
  return [isRequired ? KICKOFF_SIMPLE_FIELD_RULE : EMPTY_RULE];
}

function getCheckboxValidateRules({ isRequired }: IExtraField) {
  return [
    isRequired
      ? {
          message: 'validation.kickoff-form-field-empty',
          isInvalid: (value: string[]) => !isArrayWithItems(value),
        }
      : EMPTY_RULE,
  ];
}

function getCreatableValidateRules({ isRequired }: IExtraField) {
  return [isRequired ? KICKOFF_SIMPLE_FIELD_RULE : EMPTY_RULE];
}

function getRadioValidateRules({ isRequired }: IExtraField) {
  return [isRequired ? KICKOFF_SIMPLE_FIELD_RULE : EMPTY_RULE];
}

function getUserValidateRules({ isRequired }: IExtraField) {
  return [isRequired ? KICKOFF_SIMPLE_FIELD_RULE : EMPTY_RULE];
}
