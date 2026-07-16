import * as React from 'react';
import { useIntl } from 'react-intl';

import { ELLIPSIS_CHAR } from '../../../constants/defaultValues';
import styles from '../RichText.css';

interface IRichTextMoreLinkProps {
  onExpand: (e: React.MouseEvent<HTMLButtonElement> | React.KeyboardEvent<HTMLButtonElement>) => void;
}

export const RichTextMoreLink = ({ onExpand }: IRichTextMoreLinkProps) => {
  const { formatMessage } = useIntl();

  return (
    <button
      type="button"
      onClick={onExpand}
      className={styles['more-link']}
    >
      <span className={styles['more-link__delimiter']}>{ELLIPSIS_CHAR}</span>
      {formatMessage({ id: 'templates.description-more' })}
    </button>
  );
};
