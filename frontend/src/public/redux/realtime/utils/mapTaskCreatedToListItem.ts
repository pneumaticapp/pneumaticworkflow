import { formatDateToISOInTask } from '../../../utils/dateTime';
import type { ITaskListItem } from '../../../types/tasks';

import type { IWsTaskCreatedData } from '../types';

export function mapTaskCreatedDataToListItem(data: IWsTaskCreatedData): ITaskListItem {
  return formatDateToISOInTask({
    ...data,
    dateStarted: data.dateStartedTsp,
    dueDate: data.dueDateTsp,
    dateCompletedTsp: null,
  }) as ITaskListItem;
}
