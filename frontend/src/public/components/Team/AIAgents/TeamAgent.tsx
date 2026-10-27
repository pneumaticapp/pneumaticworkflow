import * as React from 'react';
import { useState } from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { Dropdown, Header } from '../../UI';
import type { TDropdownOption } from '../../UI';
import { WarningPopup } from '../../UI/WarningPopup';
import { MoreIcon } from '../../icons';
import { deleteAIAgent, updateAIAgent } from '../../../redux/ai/slice';
import { EditAIAgentModal } from './EditAIAgentModal';
import { getAgentInitials } from './utils/getAgentInitials';
import type { ITeamAgentProps } from './types';

import styles from './TeamAgent.css';

export function TeamAgent({ agent, providerName }: ITeamAgentProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const initials = getAgentInitials(agent.name);

  const handleOpenEditModal = () => {
    setIsEditModalOpen(true);
  };

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
  };

  const handleOpenDeleteModal = () => {
    setIsDeleteModalOpen(true);
  };

  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false);
  };

  const handleToggleActive = (checked: boolean) => {
    dispatch(updateAIAgent({ id: agent.id, isActive: checked }));
  };

  const handleConfirmDelete = () => {
    dispatch(deleteAIAgent(agent.id));
  };

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'team.ai-agents.edit' }),
      onClick: handleOpenEditModal,
    },
    {
      label: formatMessage({ id: 'team.ai-agents.delete' }),
      onClick: handleOpenDeleteModal,
      color: 'red',
      withUpperline: true,
    },
  ];

  return (
    <article className={styles['agent-card']} data-testid={`ai-agent-${agent.id}`}>
      <div className={styles['agent-card__avatar']}>{agent.photo ? <img src={agent.photo} alt="" /> : initials}</div>
      <div className={styles['agent-card__info']}>
        <Header tag="h3" size="6" className={styles['agent-card__name']}>
          {agent.name}
        </Header>
        <p className={styles['agent-card__meta']}>
          {providerName ?? formatMessage({ id: 'team.ai-agents.unknown-provider' })}
          {' · '}
          {agent.model}
        </p>
        {!agent.isActive && (
          <span className={styles['agent-card__inactive']} data-testid={`ai-agent-inactive-${agent.id}`}>
            {formatMessage({ id: 'team.ai-agents.inactive' })}
          </span>
        )}
      </div>
      <div className={styles['agent-card__actions']}>
        <div className={styles['agent-card__toggle']}>
          <span>{formatMessage({ id: 'team.ai-agents.active-toggle' })}</span>
          <Switch
            checked={agent.isActive}
            onChange={handleToggleActive}
            checkedChildren={null}
            unCheckedChildren={null}
            className="custom-switch custom-switch-primary custom-switch-small"
            data-testid={`ai-agent-toggle-${agent.id}`}
          />
        </div>
        <Dropdown
          toggleProps={{ 'data-testid': `ai-agent-more-${agent.id}` }}
          renderToggle={(isOpen) => (
            <MoreIcon className={classnames(styles['agent-card__more'], isOpen && styles['agent-card__more_active'])} />
          )}
          options={dropdownOptions}
        />
      </div>

      {isEditModalOpen && <EditAIAgentModal agent={agent} onClose={handleCloseEditModal} />}

      <WarningPopup
        isOpen={isDeleteModalOpen}
        title={formatMessage({ id: 'team.ai-agents.delete-modal-title' })}
        message={formatMessage({ id: 'team.ai-agents.delete-confirm' }, { name: agent.name })}
        acceptTitle={formatMessage({ id: 'team.ai-agents.delete' })}
        declineTitle={formatMessage({ id: 'integrations.cancel' })}
        onConfirm={handleConfirmDelete}
        onReject={handleCloseDeleteModal}
        closeModal={handleCloseDeleteModal}
      />
    </article>
  );
}
