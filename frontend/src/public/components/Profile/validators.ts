/* eslint-disable */
/* prettier-ignore */
import { hasWhitespaces, IRule, isEmpty, validateFieldCreator } from '../../utils/validators';

export const OLD_PASSWORD_RULES: IRule[] = [
  {
    message: 'validation.old-password-empty',
    isInvalid: isEmpty,
  },
];

export const NEW_PASSWORD_RULES: IRule[] = [
  {
    message: 'validation.new-password-empty',
    isInvalid: isEmpty,
  },
  {
    message: 'validation.change-password-field-too-short',
    isInvalid: value => value.length !== 0 && value.length < 6,
  },
  {
    message: 'validation.change-password-field-contain-spaces',
    isInvalid: hasWhitespaces,
  },
];

export const validateOldPassword = validateFieldCreator(OLD_PASSWORD_RULES);
export const validateNewPassword = validateFieldCreator(NEW_PASSWORD_RULES);
