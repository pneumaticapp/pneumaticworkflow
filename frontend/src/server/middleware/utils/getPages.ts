import { logServerError } from '../../utils/expectedErrors';
import { serverApi } from '../../utils';
import { getConfig } from '../../../public/utils/getConfig';
import { IPages } from '../../../public/redux/pages/types';

const {
  api: { urls },
} = getConfig();

export async function getPages() {
  try {
    return await serverApi.get<IPages>(urls.getPages);
  } catch (error) {
    logServerError('failed to get pages: ', error);
  }

  return null;
}
