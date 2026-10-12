import * as React from 'react';
import { useEffect, useState } from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { IAIAgent } from '../../../types/ai';
import { TITLES } from '../../../constants/titles';
import { EPageTitle } from '../../../constants/defaultValues';
import { ERoutes } from '../../../constants/routes';
import { history } from '../../../utils/history';
import { PageTitle } from '../../PageTitle/PageTitle';
import { AddButton } from '../../UI/Buttons/AddButton';
import { Button } from '../../UI/Buttons/Button';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import { Dropdown, TDropdownOption } from '../../UI';
import { MoreIcon } from '../../icons';
import { TeamUserSkeleton } from '../TeamUserSkeleton';
import { CreatePerformerModal } from '../Users/CreatePerformerModal';
import { ECreatePerformerModalTab } from '../Users/CreatePerformerModal/types';
import { deleteAIAgent, loadAIAgents, loadAIProviders, updateAIAgent } from '../../../redux/ai/slice';
import { getAIAgentsState, getAIProvidersState, getIsAISaving } from '../../../redux/selectors/ai';

import { EditAIAgentModal } from './EditAIAgentModal';
import styles from './AIAgents.css';

export function AIAgents() {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const { list: agents, isLoading } = useSelector(getAIAgentsState);
  const { list: providers, isLoading: areProvidersLoading } = useSelector(getAIProvidersState);
  const isSaving = useSelector(getIsAISaving);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [agentToEdit, setAgentToEdit] = useState<IAIAgent | null>(null);
  const [agentToDelete, setAgentToDelete] = useState<IAIAgent | null>(null);

  useEffect(() => {
    document.title = TITLES.Team;
    dispatch(loadAIAgents());
    dispatch(loadAIProviders());
  }, []);

  const providerNameById = new Map(providers.map((provider) => [provider.id, provider.name]));

  const handleToggleActive = (agent: IAIAgent) => (checked: boolean) => {
    dispatch(updateAIAgent({ id: agent.id, isActive: checked }));
  };

  const handleConfirmDelete = () => {
    if (agentToDelete) {
      dispatch(deleteAIAgent(agentToDelete.id));
      setAgentToDelete(null);
    }
  };

  const renderInitials = (name: string) =>
    name
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((word) => word.charAt(0))
      .join('')
      .toUpperCase();

  const getAgentDropdownOptions = (agent: IAIAgent): TDropdownOption[] => [
    {
      label: formatMessage({ id: 'team.ai-agents.edit' }),
      onClick: () => setAgentToEdit(agent),
    },
    {
      label: formatMessage({ id: 'team.ai-agents.delete' }),
      onClick: () => setAgentToDelete(agent),
      color: 'red',
      withUpperline: true,
    },
  ];

  const renderAgentCard = (agent: IAIAgent) => (
    <div key={agent.id} className={styles['agent-card']} data-testid={`ai-agent-${agent.id}`}>
      <div className={styles['agent-card__avatar']}>
        {agent.photo ? <img src={agent.photo} alt="" /> : renderInitials(agent.name)}
      </div>
      <div className={styles['agent-card__info']}>
        <span className={styles['agent-card__name']}>{agent.name}</span>
        <span className={styles['agent-card__meta']}>
          {providerNameById.get(agent.providerId) ?? formatMessage({ id: 'team.ai-agents.unknown-provider' })}
          {' · '}
          {agent.model}
        </span>
        {!agent.isActive && (
          <span className={styles['agent-card__inactive']} data-testid={`ai-agent-inactive-${agent.id}`}>
            {formatMessage({ id: 'team.ai-agents.inactive' })}
          </span>
        )}
      </div>
      <div className={styles['agent-card__actions']}>
        <div className={styles['agent-card__toggle']}>
          <span>{formatMessage({ id: 'team.ai-agents.active-toggle' })}</span>
          <div data-testid={`ai-agent-toggle-${agent.id}`}>
            <Switch
              checked={agent.isActive}
              disabled={isSaving}
              onChange={handleToggleActive(agent)}
              checkedChildren={null}
              unCheckedChildren={null}
              className="custom-switch custom-switch-primary custom-switch-small"
            />
          </div>
        </div>
        <Dropdown
          toggleProps={{ 'data-testid': `ai-agent-more-${agent.id}` }}
          renderToggle={(isOpen) => (
            <MoreIcon className={classnames(styles['agent-card__more'], isOpen && styles['agent-card__more_active'])} />
          )}
          options={getAgentDropdownOptions(agent)}
        />
      </div>
    </div>
  );

  return (
    <div className={styles['container']}>
      <CreatePerformerModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        initialTab={ECreatePerformerModalTab.AIAgent}
      />
      <EditAIAgentModal agent={agentToEdit} onClose={() => setAgentToEdit(null)} />

      <PageTitle titleId={EPageTitle.Team} withUnderline={false} />

      {!areProvidersLoading && providers.length === 0 ? (
        <div className={styles['no-providers']} data-testid="no-ai-providers-hint">
          <p className={styles['no-providers__text']}>
            {formatMessage({ id: 'team.create-ai-agent-modal.no-providers-hint' })}
          </p>
          <Button
            type="button"
            size="md"
            buttonStyle="yellow"
            label={formatMessage({ id: 'team.ai-agents.go-to-providers' })}
            onClick={() => history.push(ERoutes.Integrations)}
            data-testid="go-to-ai-providers"
          />
        </div>
      ) : (
        <div className={styles['buttons-row']}>
          <AddButton
            title={formatMessage({ id: 'team.ai-agents.create-button' })}
            caption={formatMessage({ id: 'team.ai-agents.create-button-caption' })}
            onClick={() => setIsCreateModalOpen(true)}
          />
        </div>
      )}

      {!isLoading && agents.length === 0 && (
        <p className={styles['empty']} data-testid="empty-ai-agents-message">
          {formatMessage({ id: 'team.ai-agents.empty' })}
        </p>
      )}

      <div className={styles['cards']}>
        {isLoading && Array.from([1, 2, 3], (key) => <TeamUserSkeleton key={key} />)}
        {!isLoading && agents.map(renderAgentCard)}
      </div>

      <Modal isOpen={agentToDelete !== null} onClose={() => setAgentToDelete(null)} width="sm">
        <div data-testid="delete-ai-agent-modal">
          <Header tag="p" size="6" className={styles['delete-modal__title']}>
            {formatMessage({ id: 'team.ai-agents.delete-modal-title' })}
          </Header>
          <p className={styles['delete-modal__text']}>
            {formatMessage({ id: 'team.ai-agents.delete-confirm' }, { name: agentToDelete?.name ?? '' })}
          </p>
          <div className={styles['delete-modal__footer']}>
            <Button
              type="button"
              onClick={handleConfirmDelete}
              size="md"
              buttonStyle="yellow"
              label={formatMessage({ id: 'team.ai-agents.delete' })}
              data-testid="confirm-delete-ai-agent"
            />
            <button
              type="button"
              className="cancel-button"
              onClick={() => setAgentToDelete(null)}
              data-testid="cancel-delete-ai-agent"
            >
              {formatMessage({ id: 'integrations.cancel' })}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
