/* eslint-disable */
/* prettier-ignore */
import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  addWebhooks,
  removeWebhooks,
} from '../../../../redux/webhooks/actions';
import {
  EWebhooksSubscriberStatus,
  EWebhooksTypeEvent,
  IWebhookUrl,
} from '../../../../types/webhooks';
import {
  isEmpty,
  isInvalidUrlWithProtocol,
  validateFieldCreator,
} from '../../../../utils/validators';
import { InputField } from '../../../UI/Fields/InputField/InputField';
import { Button } from '../../../UI/Buttons/Button/Button';

import styles from './WebhooksItem.css';
import { useIntl } from 'react-intl';

export interface IWebhookItemProps {
  url: IWebhookUrl;
  status: EWebhooksSubscriberStatus;
  event: EWebhooksTypeEvent;
}

export function WebhookItem({ event, url, status }: IWebhookItemProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();

  const [webhookUrlState, setWebhookUrlState] = useState(url || '');
  const [webhookUrlError, setWebhookUrlError] = useState('');

  const isLoading = status === EWebhooksSubscriberStatus.Loading;
  const value = isLoading ? 'Loading...' : webhookUrlState;

  const WEBHOOKS_TITLES = {
    [EWebhooksTypeEvent.workflowStarted]: formatMessage({
      id: 'template.intergrations-webhook-title-workflowStarted',
    }),
    [EWebhooksTypeEvent.workflowCompleted]: formatMessage({
      id: 'template.intergrations-webhook-title-workflowCompleted',
    }),
    [EWebhooksTypeEvent.taskCompleted]: formatMessage({
      id: 'template.intergrations-webhook-title-taskCompleted',
    }),
    [EWebhooksTypeEvent.taskReturned]: formatMessage({
      id: 'template.intergrations-webhook-title-taskReturned',
    }),
  };

  const onSubscribe = () => {
    const validateUrl = validateFieldCreator([
      {
        message: 'validation.url-empty',
        isInvalid: isEmpty,
      },
      {
        message: 'validation.url-invalid',
        isInvalid: isInvalidUrlWithProtocol,
      },
    ]);

    const errorMessage = validateUrl(webhookUrlState);

    if (errorMessage) {
      setWebhookUrlError(errorMessage);

      return;
    }

    dispatch(
      addWebhooks({
        event,
        url: webhookUrlState,
      }),
    );
  };

  const onUnsubscribe = () => {
    dispatch(removeWebhooks({ event }));
  };

  const onKeyPress: React.DOMAttributes<HTMLInputElement>['onKeyPress'] = (
    event,
  ) => {
    if (
      event.key === 'Enter' &&
      status !== EWebhooksSubscriberStatus.Subscribed
    ) {
      onSubscribe();
    }
  };

  const onChangeWebhookUrl = (event: React.FormEvent<HTMLInputElement>) => {
    if (status !== EWebhooksSubscriberStatus.NotSubscribed) {
      return;
    }
    setWebhookUrlError('');
    setWebhookUrlState(event.currentTarget.value);
  };

  useEffect(() => {
    setWebhookUrlState(url || '');
  }, [url]);

  return (
    <div className={styles['webhook']}>
      <p className={styles['webhook-title']}>{WEBHOOKS_TITLES[event]}</p>
      <div className={styles['webhook-container']}>
        <InputField
          fieldSize="md"
          value={value}
          placeholder={'URL'}
          errorMessage={webhookUrlError}
          onKeyPress={onKeyPress}
          onChange={onChangeWebhookUrl}
        />
        <Button
          className={styles['webhooks-button']}
          type="button"
          size="sm"
          label={
            status === EWebhooksSubscriberStatus.Subscribed
              ? formatMessage({
                  id: 'template.intergrations-webhook-unsubscribe',
                })
              : formatMessage({
                  id: 'template.intergrations-webhook-subscribe',
                })
          }
          onClick={
            status === EWebhooksSubscriberStatus.Subscribed
              ? onUnsubscribe
              : onSubscribe
          }
          isLoading={[
            EWebhooksSubscriberStatus.Loading,
            EWebhooksSubscriberStatus.Subscribing,
            EWebhooksSubscriberStatus.Unsubscribing,
          ].includes(status)}
        />
      </div>
    </div>
  );
}
