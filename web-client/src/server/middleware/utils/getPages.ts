import { logger } from '../../../public/utils/logger';
import { serverApi } from '../../utils';
import { IAuthenticatedUser } from '../../utils/types';
import { getConfig } from '../../../public/utils/getConfig';

const {
  api: { urls },
} = getConfig();

export async function getPages() {
  try {
    return await serverApi.get<IAuthenticatedUser>(urls.getPages);
  } catch (error) {
    logger.error('failed to get pages: ', error);

    throw error;
  }
}
