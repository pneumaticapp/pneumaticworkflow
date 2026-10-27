import * as React from 'react';
import { useEffect } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { AddButton } from '../../UI/Buttons/AddButton';
import { Button } from '../../UI/Buttons/Button';
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
import { getAIAgentsState, getAIProvidersState } from '../../../redux/selectors/ai';

import styles from './AIAgents.css';

export function AIAgents() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { list: agents, isLoading: areAgentsLoading } = useSelector(getAIAgentsState);
  const { list: providers, isLoading: areProvidersLoading } = useSelector(getAIProvidersState);
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
  const hasNoProviders = !areProvidersLoading && providers.length === 0;
  const sortedAgents = [...agents].sort((first, second) => first.name.localeCompare(second.name));

  const renderAgents = () => {
    if (areAgentsLoading) {
      return Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />);
    }

    if (sortedAgents.length === 0) {
      return (
        <p className={styles['empty']} data-testid="empty-ai-agents-message">
          {formatMessage({ id: 'team.ai-agents.empty' })}
        </p>
      );
    }

    return (
      <ul className={styles['list']}>
        {sortedAgents.map((agent) => (
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
        onClose={() => dispatch(closeCreateUserModal())}
      />

      <PageTitle titleId={EPageTitle.Team} withUnderline={false} />

      <AddButton
        title={formatMessage({ id: 'team.ai-agents.create-button' })}
        caption={formatMessage({ id: 'team.ai-agents.create-button-caption' })}
        disabled={hasNoProviders}
        onClick={() => dispatch(openCreateUserModal())}
      />

      {hasNoProviders && (
        <div className={styles['no-providers']} data-testid="no-ai-providers-hint">
          <p className={styles['no-providers__hint']}>
            {formatMessage({ id: 'team.create-ai-agent-modal.no-providers-hint' })}
          </p>
          <Button
            type="button"
            size="md"
            buttonStyle="yellow"
            label={formatMessage({ id: 'team.create-ai-agent-modal.go-to-integrations' })}
            onClick={() => history.push(ERoutes.Integrations)}
          />
        </div>
      )}

      {renderAgents()}
    </div>
  );
}
