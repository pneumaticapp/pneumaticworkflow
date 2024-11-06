import { DEFAULT_ERROR_CODE, getErrorMessage } from '../getErrorMessage';

export function getGoogleErrorMessage(error: Error) {
  if (!(error instanceof Error)) {
    return getErrorMessage({ code: DEFAULT_ERROR_CODE, message: '' });
  }

  const googleErrorsCodes: { [key: string]: string } = {
    'Invalid Input': 'error__google_invites__no_gsuite',
    'Service unavailable. Please try again': 'error__google_invites__failed_domain',
  };

  const errorCode = googleErrorsCodes[error.message] || DEFAULT_ERROR_CODE;

  return getErrorMessage({ code: errorCode, message: error.message });
}
