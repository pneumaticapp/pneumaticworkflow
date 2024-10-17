import * as React from 'react';
import classnames from 'classnames';
import { injectIntl, IntlShape } from 'react-intl';

import { ExtraFieldString } from './String';
import { ExtraFieldText } from './Text';
import { ExtraFieldUrl } from './Url';
import { ExtraFieldDate } from './Date';
import { ExtraFieldCheckbox } from './Checkbox';
import { ExtraFieldRadio } from './Radio';
import { ExtraFieldCreatable } from './Creatable';
import { ExtraFieldFile } from './File';
import { ExtraFieldUser } from './User';

import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../types/template';
import { EInputNameBackgroundColor } from '../../../types/workflow';
import { ExtraFieldDropdown } from './utils/ExtraFieldDropdown';
import { getInputNameBackground } from './utils/getInputNameBackground';

import styles from '../KickoffRedux/KickoffRedux.css';

export interface IWorkflowExtraFieldProps {
  field: IExtraField;
  intl: IntlShape;
  showDropdown?: boolean;
  mode?: EExtraFieldMode;
  namePlaceholder?: string;
  descriptionPlaceholder?: string;
  labelBackgroundColor?: EInputNameBackgroundColor;
  deleteField?(): void;
  moveFieldUp?(): void;
  moveFieldDown?(): void;
  editField(changedProps: Partial<IExtraField>): void;
  isDisabled?: boolean;
  innerRef?: React.Ref<HTMLInputElement>;
  accountId: number;
}

interface IExtraFieldProps extends IWorkflowExtraFieldProps {
  wrapperClassName?: string;
  fieldsCount?: number;
  id?: number;
}

function ExtraField(props: IExtraFieldProps) {
  const {
    field,
    field: { apiName, isRequired = false },
    fieldsCount,
    showDropdown = true,
    deleteField,
    moveFieldUp,
    moveFieldDown,
    editField,
    isDisabled = false,
    id,
    wrapperClassName,
    labelBackgroundColor,
    innerRef,
  } = props;

  const handleDeleteField = React.useCallback(() => {
    if (!deleteField) {
      return;
    }

    deleteField();
  }, [deleteField]);

  const handleMoveFieldUp = () => {
    if (!moveFieldUp) {
      return;
    }

    moveFieldUp();
  };

  const handleMoveFieldDown = () => {
    if (!moveFieldDown) {
      return;
    }

    moveFieldDown();
  };

  const renderField = () => {
    const fieldsMap: { [key in EExtraFieldType]: Function } = {
      [EExtraFieldType.Text]: ExtraFieldText,
      [EExtraFieldType.String]: ExtraFieldString,
      [EExtraFieldType.Url]: ExtraFieldUrl,
      [EExtraFieldType.Date]: ExtraFieldDate,
      [EExtraFieldType.Checkbox]: ExtraFieldCheckbox,
      [EExtraFieldType.Radio]: ExtraFieldRadio,
      [EExtraFieldType.Creatable]: ExtraFieldCreatable,
      [EExtraFieldType.File]: ExtraFieldFile,
      [EExtraFieldType.User]: ExtraFieldUser,
    };

    const Field = fieldsMap[field.type];

    return <Field {...props} innerRef={innerRef} />;
  };

  const isFirstItem = React.useMemo(() => id === 0 && id !== undefined, [id]);
  const isLastItem = React.useMemo(() => fieldsCount !== undefined && id === fieldsCount - 1, [id, fieldsCount]);

  const getFieldClassName = () => {
    const labelClassNameMap: { [key in EExtraFieldType]: string } = {
      [EExtraFieldType.Text]: 'with-label',
      [EExtraFieldType.String]: 'with-label',
      [EExtraFieldType.Url]: 'with-label',
      [EExtraFieldType.Date]: 'with-label',
      [EExtraFieldType.Checkbox]: 'without-label',
      [EExtraFieldType.Radio]: 'without-label',
      [EExtraFieldType.Creatable]: 'with-label',
      [EExtraFieldType.File]: 'with-label',
      [EExtraFieldType.User]: 'with-label',
    };

    const labelClassName = labelClassNameMap[field.type];

    return classnames(
      getInputNameBackground(labelBackgroundColor),
      wrapperClassName,
      styles[labelClassName],
      styles['kick-off-input'],
      showDropdown && !isDisabled && styles['kick-off-input_with-dropdown'],
    );
  };

  const getIsRequiredDisabled = () => {
    const isRequiredDisabledMap: { [key in EExtraFieldType]: boolean } = {
      [EExtraFieldType.Text]: false,
      [EExtraFieldType.String]: false,
      [EExtraFieldType.Url]: false,
      [EExtraFieldType.Date]: false,
      [EExtraFieldType.Checkbox]: false,
      [EExtraFieldType.Radio]: false,
      [EExtraFieldType.Creatable]: false,
      [EExtraFieldType.File]: false,
      [EExtraFieldType.User]: true,
    };

    return isRequiredDisabledMap[field.type];
  };

  return (
    <div className={getFieldClassName()}>
      {renderField()}

      {showDropdown && !isDisabled && (
        <div className={styles['kick-off-input__dropdown']}>
          <ExtraFieldDropdown
            isFirstItem={isFirstItem}
            isLastItem={isLastItem}
            apiName={apiName}
            isRequired={isRequired}
            isRequiredDisabled={getIsRequiredDisabled()}
            onEditField={editField}
            onMoveFieldUp={handleMoveFieldUp}
            onMoveFieldDown={handleMoveFieldDown}
            onDeleteField={handleDeleteField}
          />
        </div>
      )}
    </div>
  );
}

export const ExtraFieldIntl = injectIntl(ExtraField);
