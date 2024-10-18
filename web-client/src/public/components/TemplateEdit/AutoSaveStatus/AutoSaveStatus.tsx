/* eslint-disable jsx-a11y/interactive-supports-focus */
/* eslint-disable jsx-a11y/click-events-have-key-events */
import * as React from 'react';
import classnames from 'classnames';
import * as ReactDOM from 'react-dom';
import { debounce } from 'throttle-debounce';

import { InfoAlertIcon, SuccessCheckMark } from '../../icons';
import { IntlMessages } from '../../IntlMessages';
import { ETemplateStatus } from '../../../types/redux';
import { usePrevious } from '../../../hooks/usePrevious';

import styles from './AutoSaveStatus.css';

export interface IAutoSaveStatusProps {
  templateStatus: ETemplateStatus;
  withPaywall: boolean;
  onRetry(): void;
}

export function AutoSaveStatus({ templateStatus, withPaywall, onRetry }: IAutoSaveStatusProps) {
  const { useEffect, useState, useRef } = React;

  const [showSavedMessage, setShowSavedMessage] = useState(false);
  const prevWorkflowStatus = usePrevious(templateStatus);

  const debouncedHideSavedMessage = useRef(
    debounce(3000, () => {
      setShowSavedMessage(false);
    }),
  ).current;

  useEffect(() => {
    if (templateStatus === ETemplateStatus.Saved && prevWorkflowStatus === ETemplateStatus.Saving) {
      setShowSavedMessage(true);
      debouncedHideSavedMessage();
    }
  }, [templateStatus]);

  const containerClassName = classnames(styles['container'], withPaywall && styles['container__with-paywall']);

  const renderStatus = () => {
    if (templateStatus === ETemplateStatus.SaveFailed) {
      return (
        <div className={containerClassName}>
          <p className={classnames(styles['message'], styles['failed'])}>
            <InfoAlertIcon className={styles['icon']} />
            <IntlMessages id="template.save-failed" />
            <IntlMessages id="templates.save-retry">
              {(text) => (
                <span role="button" onClick={onRetry} className={styles['retry']}>
                  {text}
                </span>
              )}
            </IntlMessages>
          </p>
        </div>
      );
    }

    if (!showSavedMessage) {
      return null;
    }

    return (
      <div className={containerClassName}>
        <p className={classnames(styles['message'], styles['success'])}>
          <SuccessCheckMark className={styles['icon']} />
          <IntlMessages id="templates.save-success" />
        </p>
      </div>
    );
  };

  return ReactDOM.createPortal(renderStatus(), document.body);
}
