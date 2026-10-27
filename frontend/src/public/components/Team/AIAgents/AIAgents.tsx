import * as React from 'react';
import { useEffect } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { AddButton } from '../../UI/Buttons/AddButton';
import { Button } from '../../UI/Buttons/Button';
import { Placeholder } from '../../UI/Placeholder';
import { TasksPlaceholderIcon } from '../../Tasks/TasksPlaceholderIcon';
import { PageTitle } from '../../PageTitle';
import { TeamUserSkeleton } from '../TeamUserSkeleton';
import { TeamAgent } from './TeamAgent';
import { CreatePerformerModal } from '../Users/CreatePerformerModal';
import { ECreatePerformerModalTab } from '../Users/CreatePerformerModal/types';
import { EPageTitle } from '../../../constants/defaultValues';
import { ERoutes } from '../../../constants/routes';
import { TITLES } from '../../../constants/titles';
import { history } from '../../../utils/history';
import { closeCreateUserModal, openCreateUserModal } from '../../../redux/accounts/slice';
import { loadAIAgents, loadAIProviders } from '../../../redux/ai/slice';
import { getIsCreateUserModalOpen } from '../../../redux/selectors/accounts';
import { getAIAgentsSortedByName, getAIAgentsState, getAIProvidersState } from '../../../redux/selectors/ai';

import styles from './AIAgents.css';

export function AIAgents() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { isLoading: isAgentsLoading } = useSelector(getAIAgentsState);
  const agents = useSelector(getAIAgentsSortedByName);
  const { list: providers, isLoading: isProvidersLoading } = useSelector(getAIProvidersState);
  const isCreateModalOpen = useSelector(getIsCreateUserModalOpen);

  useEffect(() => {
    dispatch(loadAIAgents());
    dispatch(loadAIProviders());
    document.title = TITLES.Team;

    return () => {
      dispatch(closeCreateUserModal());
    };
  }, [dispatch]);

  const providerNameById = new Map(providers.map((provider) => [provider.id, provider.name]));
  const hasNoProviders = !isProvidersLoading && providers.length === 0;

  const handleOpenCreateModal = () => {
    dispatch(openCreateUserModal());
  };

  const handleCloseCreateModal = () => {
    dispatch(closeCreateUserModal());
  };

  const handleGoToIntegrations = () => {
    history.push(ERoutes.Integrations);
  };

  const renderAgents = () => {
    if (isAgentsLoading) {
      return Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);
    }

    if (agents.length === 0) {
      return (
        <Placeholder
          title={formatMessage({ id: 'team.ai-agents.empty' })}
          description={
            hasNoProviders ? formatMessage({ id: 'team.create-ai-agent-modal.no-providers-hint' }) : undefined
          }
          Icon={TasksPlaceholderIcon}
          mood="neutral"
          footer={
            hasNoProviders && (
              <Button
                type="button"
                size="md"
                buttonStyle="yellow"
                label={formatMessage({ id: 'team.create-ai-agent-modal.go-to-integrations' })}
                onClick={handleGoToIntegrations}
              />
            )
          }
        />
      );
    }

    return (
      <ul className={styles['list']}>
        {agents.map((agent) => (
          <li key={agent.id}>
            <TeamAgent agent={agent} providerName={providerNameById.get(agent.providerId)} />
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className={styles['container']}>
      <CreatePerformerModal
        isOpen={isCreateModalOpen}
        initialTab={ECreatePerformerModalTab.AIAgent}
        onClose={handleCloseCreateModal}
      />

      <PageTitle titleId={EPageTitle.Team} withUnderline={false} />

      <AddButton
        title={formatMessage({ id: 'team.ai-agents.create-button' })}
        caption={formatMessage({ id: 'team.ai-agents.create-button-caption' })}
        disabled={hasNoProviders}
        onClick={handleOpenCreateModal}
      />

      {renderAgents()}
    </div>
  );
}
