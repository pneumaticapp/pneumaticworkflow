import * as React from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import { IFieldsetBindingClient } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';

import styles from './FieldsetOutputsPreview.css';

export interface IFieldsetOutputsPreviewProps {
  fieldsets: IFieldsetBindingClient[];
  onGroupClick?(): void;
}

export function FieldsetOutputsPreview({ fieldsets, onGroupClick }: IFieldsetOutputsPreviewProps) {
  const { formatMessage } = useIntl();

  if (!fieldsets.length) {
    return null;
  }

  const fieldsetsWithFields = fieldsets.filter((fieldset) => isArrayWithItems(fieldset.fields));

  if (!fieldsetsWithFields.length) {
    return null;
  }

  return (
    <div className={styles['fieldset-outputs-preview']}>
      {fieldsetsWithFields.map(({ apiNameBinding, name }) => (
        <button type="button" className={classNames(styles['fieldset-outputs-preview__group'])} key={apiNameBinding} onClick={onGroupClick}>
          <span className={styles['fieldset-outputs-preview__title']}>
            {formatMessage({ id: 'fieldsets.title' })}: {name}
          </span>
        </button>
      ))}
    </div>
  );
}
