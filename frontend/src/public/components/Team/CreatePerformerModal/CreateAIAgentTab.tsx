import React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { ModalBody } from '../../UI/BaseModal';
import { Button } from '../../UI/Buttons/Button';
import { Loader } from '../../UI/Loader';
import { ERoutes } from '../../../constants/routes';
import { history } from '../../../utils/history';
import { createAIAgent } from '../../../redux/ai/slice';
import { closeCreatePerformerModal } from '../../../redux/team/slice';
import { getAIProvidersIsLoading, getAIProvidersList } from '../../../redux/selectors/ai';
import { getTeamCreatePerformerModalIsSubmitting } from '../../../redux/selectors/team';
import { AIAgentForm } from '../AIAgents/AIAgentForm';
import type { IAIAgentFormValues } from '../AIAgents/AIAgentForm/types';
import type { ICreatePerformerTabProps } from './types';

import styles from './CreatePerformerModal.css';

export function CreateAIAgentTab({ isVisible }: ICreatePerformerTabProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const isLoadingProviders = useSelector(getAIProvidersIsLoading);
  const providers = useSelector(getAIProvidersList);
  const isSubmitting = useSelector(getTeamCreatePerformerModalIsSubmitting);
  const hasProviders = providers.length > 0;

  const handleSubmit = (values: IAIAgentFormValues) => {
    dispatch(
      createAIAgent({
        name: values.name.trim(),
        providerId: Number(values.providerId),
        model: values.model,
        systemPrompt: values.systemPrompt,
        photo: values.photo || null,
        isActive: true,
      }),
    );
  };

  const handleGoToIntegrations = () => {
    dispatch(closeCreatePerformerModal());
    history.push(ERoutes.Integrations);
  };

  return (
    <>
      {isVisible && isLoadingProviders && !hasProviders && (
        <ModalBody className={styles['modal__no-providers']}>
          <Loader isLoading isCentered={false} />
        </ModalBody>
      )}

      {isVisible && !isLoadingProviders && !hasProviders && (
        <ModalBody className={styles['modal__no-providers']}>
          <p className={styles['modal__no-providers-hint']} data-testid="ai-agent-no-providers-hint">
            {formatMessage({ id: 'team.create-ai-agent-modal.no-providers-hint' })}
          </p>
          <Button
            type="button"
            size="md"
            buttonStyle="yellow"
            label={formatMessage({ id: 'team.create-ai-agent-modal.go-to-integrations' })}
            onClick={handleGoToIntegrations}
            data-testid="go-to-integrations"
          />
        </ModalBody>
      )}

      <AIAgentForm
        isVisible={isVisible && hasProviders}
        isSubmitting={isSubmitting}
        submitLabel={formatMessage({ id: 'team.create-ai-agent-modal.submit' })}
        onSubmit={handleSubmit}
      />
    </>
  );
}
