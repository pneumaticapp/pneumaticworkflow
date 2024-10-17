import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function unmarkChecklistItem(checklistId: number, itemId: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.unmarkChecklistItem.replace(':id', checklistId);

  return commonRequest(
    url,
    {
      method: 'POST',
      body: mapRequestBody({
        selectionId: itemId,
      }),
    },
    {
      shouldThrow: true,
    },
  );
}
