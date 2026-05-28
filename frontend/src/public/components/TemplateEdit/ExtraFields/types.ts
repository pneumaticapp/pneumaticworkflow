import { Ref } from 'react';
import { IntlShape } from 'react-intl';

import { EExtraFieldMode, IExtraField } from '../../../types/template';
import { EInputNameBackgroundColor } from '../../../types/workflow';
import { EFieldLabelPosition } from '../../../types/fieldset';

export interface IWorkflowExtraFieldProps {
  field: IExtraField;
  intl: IntlShape;
  showDropdown?: boolean;
  mode: EExtraFieldMode;
  namePlaceholder?: string;
  descriptionPlaceholder?: string;
  labelBackgroundColor?: EInputNameBackgroundColor;
  labelPosition: EFieldLabelPosition;
  deleteField?(): void;
  moveFieldUp?(): void;
  moveFieldDown?(): void;
  editField(changedProps: Partial<IExtraField>): void;
  isDisabled?: boolean;
  innerRef?: Ref<HTMLInputElement>;
  accountId: number;
  datasetName?: string;
}

type IExtraFieldPropsBase = Omit<IWorkflowExtraFieldProps, 'showDropdown'> & {
  wrapperClassName?: string;
  fieldsCount?: number;
  id?: number;
};

export type IExtraFieldProps = IExtraFieldPropsBase & (
  | {
      showDropdown: true;
      datasetOptions: { label: string; value: string }[];
    }
  | {
      showDropdown: false;
    }
);
