import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { IGettingStartedChecklist } from '../types/dashboard';

export function getGettingStartedChecklist() {
  const { api: { urls } } = getBrowserConfigEnv();

  return commonRequest<IGettingStartedChecklist>(urls.gettingStartedChecklist, {});
}
