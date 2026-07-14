import { ETemplateStatus } from '../../../types/redux';
import { ITemplateOwner } from '../../../types/template';
import { IInfoWarningProps } from '../InfoWarningsModal';
import { TSetFieldValue } from '../useTemplateForm/types';

export interface ITemplateControllsProps {
  setInfoWarnings(infoWarnings: ((props: IInfoWarningProps) => JSX.Element)[]): void;
}

export interface ITemplateOwnersSettingsProps {
  owners: ITemplateOwner[];
  setFieldValue: TSetFieldValue;
}

export interface ITemplateMoreSettingsProps {
  templateId: number | undefined;
  onClone(): void;
  onDelete(): void;
}

export interface ITemplateNotificationSettingsProps {
  finalizable: boolean;
  completionNotification: boolean;
  reminderNotification: boolean;
  setFieldValue: TSetFieldValue;
}

export interface ITemplateNavigationProps {
  templateId: number | undefined;
  templateName: string;
  isActive: boolean;
  isDeleted: boolean;
  isDeleteModalOpen: boolean;
  onCloseDeleteModal(): void;
  onDelete(): void;
  onActivate(redirectUrl: string): void;
  onDiscard(onSuccess: () => void): void;
}

export interface ITemplateControlButtonsProps {
  isActive: boolean;
  isActivating: boolean;
  templateStatus: ETemplateStatus;
  onToggleActive(): void;
  onRun(): void;
}
