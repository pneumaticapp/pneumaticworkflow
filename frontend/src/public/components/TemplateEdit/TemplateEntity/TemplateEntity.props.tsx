import { ITemplateTaskClient } from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { EMoveDirections } from '../../../types/workflow';

export interface ITemplateEntityProps {
  index: number;
  task: ITemplateTaskClient;
  users: TUserListItem[];
  tasksCount: number;
  isSubscribed: boolean;
  isTaskOpen: boolean;
  isDelayOpen: boolean;
  actualPreviousTaskApiName?: string;
  addDelay(): void;
  addTaskBefore(): void;
  deleteDelay(targetTask: ITemplateTaskClient): () => void;
  editDelay(delay: string): void;
  toggleDelay(): void;
  handleMoveTask(from: number, direction: EMoveDirections): () => void;
  removeTask(): void;
  toggleIsOpenTask(): void;
  cloneTask(): void;
}
