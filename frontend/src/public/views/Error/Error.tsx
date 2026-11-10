/* prettier-ignore */
import * as React from 'react';
import { Link } from 'react-router-dom';
import { useIntl } from 'react-intl';

import { useDocumentTitle } from '../../hooks/useDocumentTitle';
import { Header } from '../../components/UI/Typeography/Header';
import { Button } from '../../components/UI/Buttons/Button';
import { ErrorIcon } from './ErrorIcon';
import { BRAND } from '../../constants/branding';
import { LogoContainer } from '../../components/Logo';

import styles from './Error.css';

export function Error() {
  useDocumentTitle('Error');

  const { formatMessage } = useIntl();

  React.useEffect(() => {
    document.body.classList.add('background');

    return () => {
      document.body.classList.remove('background');
    };
  });

  return (
    <div className={styles.container}>
      <a href={BRAND.homePath}>
        <LogoContainer size="lg" theme="light" className={styles['logo']} />
      </a>

      <div className={styles['error-text-container']}>
        <ErrorIcon />

        <Header className={styles.header} tag="h6" size="2">
          {formatMessage({ id: 'error.oh-no' })}
        </Header>
        <div className={styles.text}>
          {formatMessage({ id: 'error.this-page-doesnt-exist' })}
          <div>{formatMessage({ id: 'error.you-may-mistyped' })}</div>
        </div>

        <Button
          buttonStyle="yellow"
          className={styles['back-button']}
          label={formatMessage({ id: 'error.back-to-the-home-page' })}
          to="/"
          wrapper={Link}
          size="md"
        />
      </div>

      <div className={styles.copyright}>
        {formatMessage(
          { id: 'public-form.copyright' },
          {
            link: (
              <a className={styles['copyright__link']} href={BRAND.homePath} target="_blank" rel="noreferrer">
                {formatMessage({ id: 'public-form.pneumatic' })}
              </a>
            ),
          },
        )}
      </div>
    </div>
  );
}
