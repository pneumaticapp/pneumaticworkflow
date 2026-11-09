/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { RouteComponentProps } from 'react-router-dom';
import { useIntl } from 'react-intl';

import { TLoadIntegrationDetailsPayload } from '../../redux/actions';
import { IIntegrationDetailed } from '../../types/integrations';
import { Loader } from '../UI/Loader';
import { useDocumentTitle } from '../../hooks/useDocumentTitle';
import { Button } from '../UI/Buttons/Button';

import styles from './IntegrationDetails.css';

export interface ITaskDetailPathParams {
  id: string;
}

export interface IIntegrationDetailsProps extends RouteComponentProps {
  integration: IIntegrationDetailed | null;
  isLoading: boolean;
  loadIntegrationDetails({ id }: TLoadIntegrationDetailsPayload): void;
}

export function IntegrationDetails({
  integration,
  isLoading,
  match,
  loadIntegrationDetails,
}: IIntegrationDetailsProps) {
  const { useEffect } = React;
  const { messages } = useIntl();
  useDocumentTitle('Integrations', integration?.name || undefined);

  useEffect(() => {
    const { id: taskId } = match.params as ITaskDetailPathParams;

    const normalizedIntegrationId = Number(taskId);

    loadIntegrationDetails({ id: normalizedIntegrationId });
  }, []);

  const renderButton = () => {
    if (!integration?.url) {
      return null;
    }

    const buttonText = integration?.buttonText || (messages['integrations.connect-account'] as string);

    return <Button wrapper="a" href={integration?.url} target="_blank" label={buttonText} buttonStyle="yellow" />;
  };

  const renderIntegration = () => {
    if (isLoading) {
      return <Loader isLoading={true} />;
    }

    return (
      <div className={styles['integraion']}>
        {integration?.logo && (
          <div className={styles['logo-container']}>
            <img className={styles['logo']} src={integration?.logo} alt={integration?.name} />
          </div>
        )}

        {integration?.longDescription && (
          <div className={styles['description']} dangerouslySetInnerHTML={{ __html: integration?.longDescription }} />
        )}

        {renderButton()}
      </div>
    );
  };

  return <div className={styles['container']}>{renderIntegration()}</div>;
}
