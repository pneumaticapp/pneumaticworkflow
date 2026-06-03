import { formatDateToISOInTask } from '../../../utils/dateTime';
import type { ITaskListItem } from '../../../types/tasks';

import type { IWsTaskCreatedData } from '../wsPayloads';

export function mapTaskCreatedDataToListItem(data: IWsTaskCreatedData): ITaskListItem {
  return formatDateToISOInTask({
    ...data,
    dateCompletedTsp: null,
  }) as ITaskListItem;
}
