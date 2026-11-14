import { commonRequest } from '../commonRequest';
import { getBrowserConfigEnv } from '../../utils/getConfig';

import type { ITemplateResponse } from '../../types/template';

export function getFaq() {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  return commonRequest<ITemplateResponse>(urls.getFaq);
}
