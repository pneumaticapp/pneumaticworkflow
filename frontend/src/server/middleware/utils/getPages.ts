import { logger } from '../../../public/utils/logger';
import { serverApi } from '../../utils';
import { getConfig } from '../../../public/utils/getConfig';
import { IPages } from '../../../public/types/page';

const {
  api: { urls },
} = getConfig();

export async function getPages() {
  try {
    return await serverApi.get<IPages>(urls.getPages);
  } catch (error) {
    logger.error('failed to get pages: ', error);
  }

  return null;
}
