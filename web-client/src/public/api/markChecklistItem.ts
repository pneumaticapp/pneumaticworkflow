import { commonRequest } from './commonRequest';
import { getBrowserConfigEnv } from '../utils/getConfig';
import { mapRequestBody } from '../utils/mappers';

export function markChecklistItem(checklistId: number, itemId: number) {
  const {
    api: { urls },
  } = getBrowserConfigEnv();

  const url = urls.markChecklistItem.replace(':id', checklistId);

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
