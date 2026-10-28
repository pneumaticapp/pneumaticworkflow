import * as React from 'react';
import { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { BaseModal, ModalHeader, ModalBody } from '../../UI/BaseModal';
import { Button } from '../../UI/Buttons/Button';
import { Loader } from '../../UI/Loader';
import { Tabs } from '../../UI/Tabs';
import { ERoutes } from '../../../constants/routes';
import { history } from '../../../utils/history';
import { createAIAgent, loadAIProviders } from '../../../redux/ai/slice';
import { getAICreateAgentIsLoading, getAIProvidersIsLoading, getAIProvidersList } from '../../../redux/selectors/ai';

import { AIAgentForm } from '../AIAgents/AIAgentForm';
import type { IAIAgentFormValues } from '../AIAgents/AIAgentForm/types';
import { CreateUserForm } from './CreateUserForm';
import type { ICreatePerformerModalProps } from './types';
import { ECreatePerformerModalTab } from './types';

import styles from './CreatePerformerModal.css';

export function CreatePerformerModal({
  isOpen,
  onClose,
  initialTab = ECreatePerformerModalTab.User,
}: ICreatePerformerModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const [activeTab, setActiveTab] = useState(initialTab);
  const [formsKey, setFormsKey] = useState(0);
  const isLoadingProviders = useSelector(getAIProvidersIsLoading);
  const providers = useSelector(getAIProvidersList);
  const isCreatingAgent = useSelector(getAICreateAgentIsLoading);

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      setFormsKey((key) => key + 1);
      dispatch(loadAIProviders());
    }
  }, [dispatch, isOpen, initialTab]);

  const handleCreateAIAgent = (values: IAIAgentFormValues) => {
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
    onClose();
    history.push(ERoutes.Integrations);
  };

  const hasProviders = providers.length > 0;
  const isAIAgentTab = activeTab === ECreatePerformerModalTab.AIAgent;

  return (
    <BaseModal
      isOpen={isOpen}
      toggle={onClose}
      className={styles['modal__dialog']}
      contentClassName={styles['modal__content']}
    >
      <ModalHeader toggle={onClose} className={styles['modal__header']} titleTag="div">
        <Tabs
          values={[
            { id: ECreatePerformerModalTab.User, label: formatMessage({ id: 'team.create-user-modal.tab-user' }) },
            {
              id: ECreatePerformerModalTab.AIAgent,
              label: formatMessage({ id: 'team.create-user-modal.tab-ai-agent' }),
            },
          ]}
          activeValueId={activeTab}
          variant="pill"
          onChange={setActiveTab}
        />
      </ModalHeader>

      {isAIAgentTab && isLoadingProviders && !hasProviders && (
        <ModalBody className={styles['modal__no-providers']}>
          <Loader isLoading isCentered={false} />
        </ModalBody>
      )}

      {isAIAgentTab && !isLoadingProviders && !hasProviders && (
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
        key={`agent-${formsKey}`}
        isVisible={isAIAgentTab && hasProviders}
        isSubmitting={isCreatingAgent}
        submitLabel={formatMessage({ id: 'team.create-ai-agent-modal.submit' })}
        onSubmit={handleCreateAIAgent}
      />
      <CreateUserForm key={`user-${formsKey}`} isVisible={activeTab === ECreatePerformerModalTab.User} />
    </BaseModal>
  );
}
