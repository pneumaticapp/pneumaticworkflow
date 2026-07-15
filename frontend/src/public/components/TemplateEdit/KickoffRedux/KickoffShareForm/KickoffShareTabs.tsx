import * as React from 'react';
import classnames from 'classnames';
import TextareaAutosize from 'react-textarea-autosize';
import Switch from 'rc-switch';
import { useIntl } from 'react-intl';

import { copyToClipboard } from '../../../../utils/helpers';
import { Button, InputField, Loader } from '../../../UI';
import { NotificationManager } from '../../../UI/Notifications';
import { noop } from '../../../../utils/noop';
import { IEmbeddedFormTabProps, ISharedFormTabProps } from './types';

import styles from './KickoffShareForm.css';

export function SharedFormTab({
  publicUrl,
  isSuccessUrlEnabled,
  successUrl,
  onToggleSuccessUrl,
  onChangeSuccessUrl,
}: ISharedFormTabProps) {
  const { formatMessage } = useIntl();
  const handleCopyShareLink = () => {
    if (!publicUrl) return;

    copyToClipboard(publicUrl);
    NotificationManager.success({ message: 'kickoff.share-link-copied' });
  };

  return (
    <>
      <p className={styles['description']}>{formatMessage({ id: 'kickoff.share-description' })}</p>

      {!publicUrl ? (
        <Loader isLoading isCentered={false} containerClassName={styles['loader']} />
      ) : (
        <>
          <p className={classnames(styles['field-title'], styles['field-title_indent'])}>
            {formatMessage({ id: 'kickoff.shared-link-title' })}
          </p>
          <InputField value={publicUrl} onChange={noop} className={styles['public-url']} fieldSize="md" />

          <div className={styles['redirect-url-container']}>
            <div className={styles['redirect-url-header']}>
              <p className={styles['field-title']}>{formatMessage({ id: 'kickoff.redirect-url-title' })}</p>

              <div className={styles['redirect-url__toggle']}>
                <p className={styles['redirect-url-toggle__label']}>
                  {formatMessage({ id: 'kickoff.redirect-url-toggle' })}
                </p>
                <Switch
                  className="custom-switch custom-switch-primary custom-switch-small ml-auto"
                  checked={isSuccessUrlEnabled}
                  checkedChildren={null}
                  unCheckedChildren={null}
                  onChange={onToggleSuccessUrl}
                />
              </div>
            </div>
            <InputField
              value={successUrl}
              onChange={onChangeSuccessUrl}
              className={styles['redirect-url__field']}
              fieldSize="md"
              disabled={!isSuccessUrlEnabled}
              placeholder={formatMessage({ id: 'kickoff.url-placeholder' })}
            />
          </div>

          <Button
            type="button"
            onClick={handleCopyShareLink}
            className={styles['copy-button']}
            label={formatMessage({ id: 'kickoff.copy-link' })}
            buttonStyle="transparent-orange"
            size="md"
          />
        </>
      )}
    </>
  );
}

export function EmbeddedFormTab({ hasAccess, embedUrl, embedCode }: IEmbeddedFormTabProps) {
  const { formatMessage } = useIntl();

  if (!hasAccess) return null;

  const handleCopyEmbedCode = () => {
    if (!embedCode) return;

    copyToClipboard(embedCode);
    NotificationManager.success({ message: 'kickoff.embed-code-copied' });
  };

  return (
    <>
      <p className={styles['description']}>{formatMessage({ id: 'kickoff.embed-description' })}</p>

      {!embedUrl ? (
        <Loader isLoading isCentered={false} containerClassName={styles['loader']} />
      ) : (
        <>
          <TextareaAutosize value={embedCode || ''} onChange={noop} className={styles['embed-code-field']} />

          <Button
            type="button"
            onClick={handleCopyEmbedCode}
            className={styles['copy-button']}
            label={formatMessage({ id: 'kickoff.copy-embed-code' })}
            buttonStyle="transparent-orange"
            size="md"
          />
        </>
      )}
    </>
  );
}
