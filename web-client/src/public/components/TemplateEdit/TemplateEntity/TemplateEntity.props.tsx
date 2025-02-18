import { ITemplateTask } from '../../../types/template';
import { TUserListItem } from '../../../types/user';
import { EMoveDirections } from '../../../types/workflow';

export interface ITemplateEntityProps {
  index: number;
  task: ITemplateTask;
  users: TUserListItem[];
  tasksCount: number;
  isSubscribed: boolean;
  isTaskOpen: boolean;
  isDelayOpen: boolean;
  addDelay(): void;
  addTaskBefore(): void;
  deleteDelay(targetTask: ITemplateTask): () => void;
  editDelay(delay: string): void;
  toggleDelay(): void;
  handleMoveTask(from: number, direction: EMoveDirections): () => void;
  removeTask(): void;
  toggleIsOpenTask(): void;
  cloneTask(): void;
}
