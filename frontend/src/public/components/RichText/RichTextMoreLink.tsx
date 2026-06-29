import * as React from 'react';
import { useIntl } from 'react-intl';

import { ELLIPSIS_CHAR } from '../../constants/defaultValues';
import styles from './RichText.css';

interface IRichTextMoreLinkProps {
  onExpand: (event: React.MouseEvent<HTMLAnchorElement> | React.KeyboardEvent<HTMLAnchorElement>) => void;
}

export const RichTextMoreLink = ({ onExpand }: IRichTextMoreLinkProps) => {
  const { formatMessage } = useIntl();

  const handleKeyDown = React.useCallback((event: React.KeyboardEvent<HTMLAnchorElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      onExpand(event);
    }
  }, [onExpand]);

  return (
    // eslint-disable-next-line jsx-a11y/anchor-is-valid
    <a
      href="#"
      role="button"
      tabIndex={0}
      onClick={onExpand}
      onKeyDown={handleKeyDown}
      className={styles['more-link']}
    >
      <span className={styles['more-link__delimiter']}>{ELLIPSIS_CHAR}</span>
      {formatMessage({ id: 'templates.description-more' })}
    </a>
  );
};
