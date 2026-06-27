import { IKickoffClient } from '../../../types/template';
import { IFieldsetRuntime } from '../../../types/fieldset';

export interface IPublicFormKickoff extends Omit<IKickoffClient, 'fieldsets'> {
  fieldsets: IFieldsetRuntime[];
}

export interface IPublicForm {
  accountId: number;
  name: string;
  description: string;
  kickoff: IPublicFormKickoff;
  showCaptcha: boolean;
}

export enum EPublicFormState {
  Loading = 'loading',
  FormNotFound = 'form-not-found',
  WaitingForAction = 'waiting-for-action',
  Submitting = 'submitting',
  Submitted = 'submitted',
}
