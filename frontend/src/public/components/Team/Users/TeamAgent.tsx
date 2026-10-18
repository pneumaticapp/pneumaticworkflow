import * as React from 'react';
import { useState } from 'react';
import classnames from 'classnames';
import Switch from 'rc-switch';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import type { IAIAgent } from '../../../api/ai/types';
import { Dropdown } from '../../UI';
import type { TDropdownOption } from '../../UI';
import { Button } from '../../UI/Buttons/Button';
import { Header } from '../../UI/Typeography/Header';
import { Modal } from '../../UI/Modal/Modal';
import { MoreIcon } from '../../icons';
import { deleteAIAgent, updateAIAgent } from '../../../redux/ai/slice';
import { getIsAISaving } from '../../../redux/selectors/ai';
import { EditAIAgentModal } from './EditAIAgentModal';
import { getAgentInitials } from './getAgentInitials';

import styles from './TeamAgent.css';

export interface ITeamAgentProps {
  agent: IAIAgent;
  providerName?: string;
}

export function TeamAgent({ agent, providerName }: ITeamAgentProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const isSaving = useSelector(getIsAISaving);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const initials = getAgentInitials(agent.name);

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'team.ai-agents.edit' }),
      onClick: () => setIsEditModalOpen(true),
    },
    {
      label: formatMessage({ id: 'team.ai-agents.delete' }),
      onClick: () => setIsDeleteModalOpen(true),
      color: 'red',
      withUpperline: true,
    },
  ];

  return (
    <div className={styles['agent-card']} data-testid={`ai-agent-${agent.id}`}>
      <div className={styles['agent-card__avatar']}>{agent.photo ? <img src={agent.photo} alt="" /> : initials}</div>
      <div className={styles['agent-card__info']}>
        <span className={styles['agent-card__name']}>{agent.name}</span>
        <span className={styles['agent-card__meta']}>
          {providerName ?? formatMessage({ id: 'team.ai-agents.unknown-provider' })}
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
              onChange={(checked) => dispatch(updateAIAgent({ id: agent.id, isActive: checked }))}
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
          options={dropdownOptions}
        />
      </div>

      {isEditModalOpen && <EditAIAgentModal agent={agent} onClose={() => setIsEditModalOpen(false)} />}

      <Modal isOpen={isDeleteModalOpen} onClose={() => setIsDeleteModalOpen(false)} width="sm">
        <div data-testid="delete-ai-agent-modal">
          <Header tag="p" size="6" className={styles['delete-modal__title']}>
            {formatMessage({ id: 'team.ai-agents.delete-modal-title' })}
          </Header>
          <p className={styles['delete-modal__text']}>
            {formatMessage({ id: 'team.ai-agents.delete-confirm' }, { name: agent.name })}
          </p>
          <div className={styles['delete-modal__footer']}>
            <Button
              type="button"
              onClick={() => {
                dispatch(deleteAIAgent(agent.id));
                setIsDeleteModalOpen(false);
              }}
              size="md"
              buttonStyle="yellow"
              label={formatMessage({ id: 'team.ai-agents.delete' })}
              data-testid="confirm-delete-ai-agent"
            />
            <button
              type="button"
              className="cancel-button"
              onClick={() => setIsDeleteModalOpen(false)}
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
