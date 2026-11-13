import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import type { IPages } from '../redux/pages/types';

export function getPages() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<IPages>(urls.getPages);
}
