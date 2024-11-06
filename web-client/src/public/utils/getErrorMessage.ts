export interface ICustomError {
  code: string;
  message: string;
  details?: {
    name: string;
    reason: string;
  };
  detail?: string;
}

export const DEFAULT_ERROR_CODE = 'error__unknown_code';
export const UNKNOWN_ERROR = 'Something Went Wrong';

const paidFeaturesErrors = [
  'error__conditions__paid_feature',
  'error__template__public_is_paid_feature',
];

const errorMapper: { [key: string]: string } = {
  [DEFAULT_ERROR_CODE]: UNKNOWN_ERROR,
  error__processes__wrong_task: 'task.not-found',
  error__google_invites__no_gsuite: 'users.google-invites-failed-domain',
  error__google_invites__failed_domain: 'users.google-invites-no-gsuite',
  error__payment__subscription_expired: '',
  error__conditions__paid_feature: 'templates.conditions.buy-plan-modal',
  error__template__public_is_paid_feature: 'template.kick-off-form-share.paid-feature',
  'Failed to fetch': 'error.fetch-failed',
};

export const getErrorMessage = (error?: ICustomError) => {
  if (!error) {
    return UNKNOWN_ERROR;
  }

  const { code, message, details, detail } = error;

  const dictionaryErrorMessage = errorMapper[code] ?? errorMapper[message];

  if (typeof dictionaryErrorMessage === 'string') {
    return dictionaryErrorMessage;
  }

  if (detail) {
    return errorMapper[detail] || detail || UNKNOWN_ERROR;
  }

  const errorDetails = details?.name && details?.reason && `${details.name}: ${details.reason}`;
  const errorMessage = [message, errorDetails].filter(Boolean).join('\n');

  return errorMessage || UNKNOWN_ERROR;
};

export const isPaidFeatureError = (error?: ICustomError) => {
  if (!error) {
    return false;
  }

  const { code } = error;

  return paidFeaturesErrors.includes(code);
};
