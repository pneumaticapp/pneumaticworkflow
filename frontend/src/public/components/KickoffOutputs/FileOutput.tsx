/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';

import { Attachments } from '../Attachments';
import { IExtraField } from '../../types/template';
import { isArrayWithItems } from '../../utils/helpers';
import { parseMarkdownToFiles } from '../../utils/parseMarkdownFiles';

import styles from './KickoffOutputs.css';

export function FileOutput({
  name,
  attachments,
  markdownValue,
}: IExtraField) {
  const { formatMessage } = useIntl();

  const renderValue = () => {
    const defaultValue = (
      <span className={styles['output__text']}>
        {formatMessage({ id: 'template.kick-off-form-unfilled-value' })}
      </span>
    );

    const files = isArrayWithItems(attachments)
      ? attachments
      : parseMarkdownToFiles(markdownValue);

    return isArrayWithItems(files) ? (
      <Attachments attachments={files} isEdit={false} />
    ) : defaultValue;
  };

  return (
    <p className={styles['output']}>
      <span className={styles['output__name']}>
        {name}
      </span>

      {renderValue()}
    </p>
  );
}
