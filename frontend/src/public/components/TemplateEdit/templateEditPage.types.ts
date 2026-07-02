import { RouteComponentProps } from 'react-router-dom';

import { IInfoWarningProps } from './InfoWarningsModal';
import { TUserListItem } from '../../types/user';
import { ITemplate } from '../../types/template';
import { TLoadTemplateVariablesSuccessPayload } from '../../redux/actions';
import { ETemplateStatus, IAuthUser } from '../../types/redux';

export interface ITemplateEditProps {
  match: any;
  location: any;
  authUser: IAuthUser;
  template: ITemplate;
  aiTemplate: ITemplate | null;
  templateStatus: ETemplateStatus;
  users: TUserListItem[];
  isSubscribed: boolean;
  loadTemplate(id: number): void;
  loadTemplateFromSystem(id: string): void;
  resetTemplateStore(): void;
  saveTemplate(): void;
  setTemplate(payload: ITemplate): void;
  setTemplateStatus(status: ETemplateStatus): void;
  loadTemplateVariablesSuccess(payload: TLoadTemplateVariablesSuccessPayload): void;
}

export type TTemplateEditProps = ITemplateEditProps & RouteComponentProps;

export interface ITemplateEditParams {
  id: string;
}

export interface ITemplateEditState {
  isInfoWarningsModaOpen: boolean;
  infoWarnings: ((props: IInfoWarningProps) => JSX.Element)[];
  openedTasks: { [key: string]: boolean };
  openedDelays: { [key: string]: boolean };
}
