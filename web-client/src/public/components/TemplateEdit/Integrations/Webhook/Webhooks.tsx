/* eslint-disable */
/* prettier-ignore */
import React from 'react';
import { useSelector } from 'react-redux';
import { WebhookItem } from './WebhooksItem';
import { EWebhooksTypeEvent } from '../../../../types/webhooks';
import { getWebhooks } from '../../../../redux/selectors/webhooks';

export function Webhooks() {
  const webhooksData = useSelector(getWebhooks);

  return (
    <>
      {Object.entries(webhooksData).map(([event, { status, url }]) => {
        return (
          <WebhookItem
            url={url}
            status={status}
            event={event as EWebhooksTypeEvent}
          />
        );
      })}
    </>
  );
}
