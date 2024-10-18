/* eslint-disable */
/* prettier-ignore */
import { EExtraFieldType } from '../../../../types/template';
import {
  TitleIcon,
  NotesIcon,
  DateIcon,
  LinkIcon,
  CheckboxIcon,
  RadioIcon,
  CreatableIcon,
  DownloadIcon,
  PeopleIcon,
} from '../../../icons';

export const ExtraFieldsMap = [
  {
    Icon: NotesIcon,
    id: EExtraFieldType.String,
    tooltipText: 'template.kick-off-form-small-text-field-tooltop-text',
    tooltipTitle: 'template.kick-off-form-small-text-field-tooltip-title',
  },
  {
    Icon: TitleIcon,
    id: EExtraFieldType.Text,
    tooltipText: 'template.kick-off-form-large-text-field-tooltop-text',
    tooltipTitle: 'template.kick-off-form-large-text-field-tooltip-title',
  },
  {
    Icon: CreatableIcon,
    id: EExtraFieldType.Creatable,
    tooltipText: 'template.kick-off-form-creatable-field-tooltop-text',
    tooltipTitle: 'template.kick-off-form-creatable-field-tooltip-title',
  },
  {
    Icon: CheckboxIcon,
    id: EExtraFieldType.Checkbox,
    tooltipText: 'template.kick-off-form-checkbox-field-tooltop-text',
    tooltipTitle: 'template.kick-off-form-checkbox-field-tooltip-title',
  },
  {
    Icon: RadioIcon,
    id: EExtraFieldType.Radio,
    tooltipText: 'template.kick-off-form-radio-field-tooltop-text',
    tooltipTitle: 'template.kick-off-form-radio-field-tooltip-title',
  },
  {
    Icon: DateIcon,
    id: EExtraFieldType.Date,
    tooltipText: 'template.kick-off-form-date-field-tooltop-text',
    tooltipTitle: 'template.kick-off-form-date-field-tooltip-title',
  },
  {
    Icon: DownloadIcon,
    id: EExtraFieldType.File,
    tooltipText: 'template.kick-off-form-attachment-field-tooltip-text',
    tooltipTitle: 'template.kick-off-form-attachment-field-tooltip-title',
  },
  {
    Icon: LinkIcon,
    id: EExtraFieldType.Url,
    tooltipText: 'template.kick-off-form-url-field-tooltop-text',
    tooltipTitle: 'template.kick-off-form-url-field-tooltip-title',
  },
  {
    Icon: PeopleIcon,
    id: EExtraFieldType.User,
    tooltipText: 'template.kick-off-form-user-field-tooltop-text',
    tooltipTitle: 'template.kick-off-form-user-field-tooltip-title',
  },
];
