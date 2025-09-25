import { Request } from 'express';

import { logger } from '../../../public/utils/logger';
import { IAuthenticatedUser } from '../../utils/types';

export async function getUserPublic(req: Request, token: string, userAgent?: string): Promise<IAuthenticatedUser | {}> {
  try {
    // For now, just return empty object to make forms work
    // TODO: Implement proper public API when it's ready
    logger.info('Public form accessed with token: ' + token);
    return {};
  } catch (error) {
    logger.error('failed to get account context: ', error);

    // Return empty user object instead of throwing to prevent forms from crashing
    return {};
  }
}
