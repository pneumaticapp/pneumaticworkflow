import { Ref } from 'react';
import { IntlShape } from 'react-intl';

import { EExtraFieldMode, IExtraField } from '../../../types/template';
import { EInputNameBackgroundColor } from '../../../types/workflow';
import { IDatasetOption } from './utils/types';

export interface IWorkflowExtraFieldProps {
  field: IExtraField;
  intl: IntlShape;
  showDropdown?: boolean;
  mode: EExtraFieldMode;
  namePlaceholder?: string;
  descriptionPlaceholder?: string;
  labelBackgroundColor?: EInputNameBackgroundColor;
  deleteField?(): void;
  moveFieldUp?(): void;
  moveFieldDown?(): void;
  editField(changedProps: Partial<IExtraField>): void;
  isDisabled?: boolean;
  innerRef?: Ref<HTMLInputElement>;
  accountId: number;
  datasetName?: string;
}

export interface IExtraFieldProps extends IWorkflowExtraFieldProps {
  wrapperClassName?: string;
  fieldsCount?: number;
  id?: number;
  datasetOptions?: IDatasetOption[];
}
