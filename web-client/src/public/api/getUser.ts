import { TAuthUserResult } from '../redux/actions';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { commonRequest } from './commonRequest';
import { setJwtCookie } from '../utils/authCookie';

export function getUser(token?: string) {
  if (token) {
    setJwtCookie(token);
  }
  const {
    api: { urls },
  } = getBrowserConfigEnv();
  const url = urls.getUser;

  return commonRequest<TAuthUserResult>(url, {}, { shouldThrow: true });
}
