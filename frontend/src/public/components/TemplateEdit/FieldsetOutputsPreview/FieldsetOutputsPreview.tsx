import * as React from 'react';
import { useIntl } from 'react-intl';
import classNames from 'classnames';

import { IExtraField, IFieldsetData, ITaskFieldset } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';

import styles from './FieldsetOutputsPreview.css';



export interface IFieldsetOutputsPreviewProps {
  fieldsets: ITaskFieldset[];
  fieldsetsByApiName: ReadonlyMap<string, IFieldsetData>;
  onGroupClick?(): void;
}

export function FieldsetOutputsPreview({ fieldsets, fieldsetsByApiName, onGroupClick }: IFieldsetOutputsPreviewProps) {
  const { formatMessage } = useIntl();

  if (!fieldsets.length) {
    return null;
  }

  const groups = fieldsets
    .map((taskFieldset) => {
      const fieldsetData = fieldsetsByApiName.get(taskFieldset.apiName);
      if (!fieldsetData || !isArrayWithItems(fieldsetData.fields)) {
        return null;
      }

      return { apiName: taskFieldset.apiName, fieldsetData, fields: fieldsetData.fields };
    })
    .filter((g): g is { apiName: string; fieldsetData: IFieldsetData; fields: IExtraField[] } => g !== null);

  if (!groups.length) {
    return null;
  }

  return (
    <div className={styles['fieldset-outputs-preview']}>
      {groups.map(({ apiName, fieldsetData }) => (
        <button type="button" className={classNames( styles['fieldset-outputs-preview__group'])} key={apiName} onClick={onGroupClick}>
          <span className={styles['fieldset-outputs-preview__title']}>
            { formatMessage({ id: 'fieldsets.title' }) }: { fieldsetData.name}
          </span>
честно         </button>
      ))}
    </div>
  );
}
