import * as React from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import { IExtraField, IFieldsetData } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';

import styles from './FieldsetOutputsPreview.css';



export interface IFieldsetOutputsPreviewProps {
  fieldsetIds: number[];
  fieldsetsById: ReadonlyMap<number, IFieldsetData>;
  onGroupClick?(): void;
}

export function FieldsetOutputsPreview({ fieldsetIds, fieldsetsById, onGroupClick }: IFieldsetOutputsPreviewProps) {
  const { formatMessage } = useIntl();

  if (!fieldsetIds.length) {
    return null;
  }

  const groups = fieldsetIds
    .map((id) => {
      const fieldset = fieldsetsById.get(id);
      if (!fieldset || !isArrayWithItems(fieldset.fields)) {
        return null;
      }

      return { id, fieldset, fields: fieldset.fields };
    })
    .filter((g): g is { id: number; fieldset: IFieldsetData; fields: IExtraField[] } => g !== null);

  if (!groups.length) {
    return null;
  }

  return (
    <div className={styles['fieldset-outputs-preview']}>
      {groups.map(({ id, fieldset }) => (
        <button type="button" className={classNames( styles['fieldset-outputs-preview__group'])} key={id} onClick={onGroupClick}>
          <span className={styles['fieldset-outputs-preview__title']}>{ formatMessage({ id: 'fieldsets.title' }) }: { fieldset.name}</span>
        </button>
      ))}
    </div>
  );
}
