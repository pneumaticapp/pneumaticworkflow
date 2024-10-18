import { isValidPhoneNumber } from 'react-phone-number-input';
import { couponRegex, emailRegex, urlRegex, urlWithProtocolRegex, whitespaceRegex } from '../constants/defaultValues';

export interface IRule {
  message: string;
  // tslint:disable-next-line: no-any
  isInvalid(value: any): boolean;
}

export const isEmpty = (value: string | null) => !value || !String(value).trim().length;
export const isInvalidUrl = (value: string | null) => {
  const singleUrlRegex = new RegExp(urlRegex, '');

  return !!value && !singleUrlRegex.test(value);
};

export const isInvalidUrlWithProtocol = (value: string | null) => {
  const singleUrlRegex = new RegExp(urlWithProtocolRegex, '');

  return !!value && !singleUrlRegex.test(value);
};

export const hasWhitespaces = (value: string) => whitespaceRegex.test(value);

export const EMPTY_RULE: IRule = {
  message: '',
  isInvalid: () => false,
};

export const EMAIL_RULES: IRule[] = [
  {
    message: 'validation.email-empty',
    isInvalid: isEmpty,
  },
  {
    message: 'validation.email-invalid',
    isInvalid: (value) => !emailRegex.test(value),
  },
];

export const WORKFLOW_NAME_RULES: IRule[] = [
  {
    message: 'validation.process-name-empty',
    isInvalid: isEmpty,
  },
  {
    message: 'validation.process-name-to-long',
    isInvalid: (value) => value.length > 120,
  },
];

export const EMAIL_INVITE_RULES: IRule[] = [
  {
    message: 'validation.email-invite-empty',
    isInvalid: isEmpty,
  },
  {
    message: 'validation.email-invalid',
    isInvalid: (value) => !emailRegex.test(value),
  },
];

export const PASSWORD_RULES: IRule[] = [
  {
    message: 'validation.password-empty',
    isInvalid: isEmpty,
  },
];

export const NAME_RULES: IRule[] = [
  {
    message: 'validation.name-empty',
    isInvalid: isEmpty,
  },
];

export const COMPANY_NAME_RULES: IRule[] = [
  {
    message: 'validation.company-name-empty',
    isInvalid: isEmpty,
  },
];

export const PHONE_NUMBER_RULES: IRule[] = [
  {
    message: 'validation.phone-number-invalid',
    isInvalid: (value) => {
      if (!value) {
        return false;
      }

      return !isValidPhoneNumber(value);
    },
  },
];

export const TASK_NAME_RULES: IRule[] = [
  {
    message: 'validation.task-name-empty',
    isInvalid: isEmpty,
  },
  {
    message: 'validation.task-name-to-long',
    isInvalid: (value) => value.length > 64,
  },
];

export const TASK_URL_RULES: IRule[] = [
  {
    message: 'validation.url-invalid',
    isInvalid: isInvalidUrl,
  },
];

export const ZIP_CODE_RULES: IRule[] = [
  {
    message: 'validation.zip-empty',
    isInvalid: isEmpty,
  },
];

export const ADDRESS_CODE_RULES: IRule[] = [
  {
    message: 'validation.address-empty',
    isInvalid: isEmpty,
  },
];

export const CITY_RULES: IRule[] = [
  {
    message: 'validation.city-empty',
    isInvalid: isEmpty,
  },
];

export const REGION_RULES: IRule[] = [
  {
    message: 'validation.region-empty',
    isInvalid: isEmpty,
  },
];

export const KICKOFF_FIELD_NAME_RULES: IRule[] = [
  {
    message: 'validation.kickoff-form-field-name-empty',
    isInvalid: isEmpty,
  },
  {
    message: 'validation.kickoff-form-field-name-too-long',
    isInvalid: (value) => value.length > 120,
  },
];

export const KICKOFF_FIELD_DESCRIPTION_RULES: IRule[] = [
  {
    message: 'validation.kickoff-form-field-empty',
    isInvalid: isEmpty,
  },
];

export const REGISTRATION_PASSWORD_RULES: IRule[] = [
  {
    message: 'validation.registration-password-field-empty',
    isInvalid: (value) => !hasWhitespaces(value) && isEmpty(value),
  },
  {
    message: 'validation.registration-password-field-contain-spaces',
    isInvalid: hasWhitespaces,
  },
  {
    message: 'validation.registration-password-field-too-short',
    isInvalid: (value) => value.length < 6,
  },
];

export const COUPON_RULES: IRule[] = [
  {
    message: 'validation.coupon-too-long',
    isInvalid: (value) => value.length > 50,
  },
  {
    message: 'validation.coupon-is-not-valid',
    isInvalid: (value) => !couponRegex.test(value) && !isEmpty(value),
  },
];

export const DELAY_RULES: IRule[] = [
  {
    message: 'template.delay-validation-hint-incorrect-value',
    isInvalid: (value) => !!value && !Number.isFinite(Number(value)),
  },
  {
    message: 'template.delay-validation-hint-exceeds',
    isInvalid: (value) => !!value && Boolean(Number(value)) && Number(value) > 999,
  },
];

export const CHECKBOX_AND_RADIO_FIELDS_RULUES: IRule[] = [
  {
    message: 'validation.kickoff-form-field-empty',
    isInvalid: isEmpty,
  },
  {
    message: 'validation.checkbox-and-radio-value-too-long',
    isInvalid: (value) => value.length > 200,
  },
];

export const TENANT_NAME_RULES: IRule[] = [
  {
    message: 'validation.tenant-name-empty',
    isInvalid: isEmpty,
  },
  {
    message: 'validation.tenant-name-to-long',
    isInvalid: (value) => value.length > 255,
  },
];

export const validateFieldCreator =
  (rules: IRule[]) =>
    (value: any): string => {
      return rules.reduce((msg, { message, isInvalid }) => (!msg && isInvalid(value) ? message : msg), '');
    };

export const validateCouponCode = validateFieldCreator(COUPON_RULES);
export const validateEmail = validateFieldCreator(EMAIL_RULES);
export const validateInviteEmail = validateFieldCreator(EMAIL_INVITE_RULES);
export const validatePassword = validateFieldCreator(PASSWORD_RULES);
export const validateName = validateFieldCreator(NAME_RULES);
export const validateCompanyName = validateFieldCreator(COMPANY_NAME_RULES);
export const validatePhone = validateFieldCreator(PHONE_NUMBER_RULES);
export const validateWorkflowName = validateFieldCreator(WORKFLOW_NAME_RULES);
export const validateTaskName = validateFieldCreator(TASK_NAME_RULES);
export const validateUrl = validateFieldCreator(TASK_URL_RULES);
export const validateZipCode = validateFieldCreator(ZIP_CODE_RULES);
export const validateAddress = validateFieldCreator(ADDRESS_CODE_RULES);
export const validateCity = validateFieldCreator(CITY_RULES);
export const validateRegion = validateFieldCreator(REGION_RULES);
export const validateKickoffFieldName = validateFieldCreator(KICKOFF_FIELD_NAME_RULES);
export const validateKickoffFieldDescription = validateFieldCreator(KICKOFF_FIELD_DESCRIPTION_RULES);
export const validateRegistrationPassword = validateFieldCreator(REGISTRATION_PASSWORD_RULES);
export const validateDelayField = validateFieldCreator(DELAY_RULES);
export const validateCheckboxAndRadioField = validateFieldCreator(CHECKBOX_AND_RADIO_FIELDS_RULUES);
export const validateTenantName = validateFieldCreator(TENANT_NAME_RULES);
