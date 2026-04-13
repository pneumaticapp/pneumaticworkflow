import * as React from 'react';
import { IExtraField, EExtraFieldMode } from '../../types/template';
import { EInputNameBackgroundColor } from '../../types/workflow';
import { ExtraFieldIntl } from '../TemplateEdit/ExtraFields';

import styles from './FieldsetFieldGroup.css';

export interface IFieldsetFieldGroupProps {
  fields: IExtraField[];
  title?: string;
  description?: string;
  onEditField: (apiName: string) => (changedProps: Partial<IExtraField>) => void;
  mode: EExtraFieldMode;
  labelBackgroundColor: EInputNameBackgroundColor;
  accountId: number;
  fieldClassName?: string;
  validationError?: string | null;
}

export function FieldsetFieldGroup({
  fields,
  title,
  description,
  onEditField,
  mode,
  labelBackgroundColor,
  accountId,
  fieldClassName,
  validationError,
}: IFieldsetFieldGroupProps) {
  return (
    <div className={styles['fieldset-group']}>
      {title && <p className={styles['fieldset-group__title']}>{title}</p>}
      {description && <p className={styles['fieldset-group__description']}>{description}</p>}
      {fields.map((field) => (
        <ExtraFieldIntl
          key={field.apiName}
          field={field}
          editField={onEditField(field.apiName)}
          showDropdown={false}
          mode={mode}
          labelBackgroundColor={labelBackgroundColor}
          namePlaceholder={field.name}
          descriptionPlaceholder={field.description}
          wrapperClassName={fieldClassName}
          accountId={accountId}
        />
      ))}
      {validationError && (
        <p className={styles['fieldset-group__error']}>{validationError}</p>
      )}
    </div>
  );
}
