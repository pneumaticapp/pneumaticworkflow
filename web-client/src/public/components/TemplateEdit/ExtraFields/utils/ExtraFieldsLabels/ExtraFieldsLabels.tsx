/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import { IExtraField } from '../../../../../types/template';
import { isArrayWithItems } from '../../../../../utils/helpers';
import { truncateString } from '../../../../../utils/truncateString';

import styles from './ExtraFieldsLabels.css';
import * as classnames from 'classnames';

interface IExtraFieldsLabelsProps {
  onClick?(): void;
  extraFields: IExtraField[];
}

const MAX_FIELD_LENGTH = 20;

export function ExtraFieldsLabels({ extraFields, onClick }: IExtraFieldsLabelsProps) {
  if (!isArrayWithItems(extraFields)) {
    return null;
  }

  const Tag = onClick ? 'button' : 'span';

  const renderLabels = () => {
    return extraFields.map((field: IExtraField) => (
      <Tag
        className={classnames(
          styles['extra-field-label'],
          (onClick && styles['extra-field-label_clickable']),
        )}
        key={`extra-field-label-${field.apiName}`}
        onClick={onClick}
      >
        {truncateString(field.name, MAX_FIELD_LENGTH)}
      </Tag>
    ));
  };

  return <>{renderLabels()}</>;
}
