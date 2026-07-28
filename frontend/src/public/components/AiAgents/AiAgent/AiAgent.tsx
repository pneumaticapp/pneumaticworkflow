import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { Dropdown, TDropdownOption } from '../../UI';
import { AIPlusIcon, MoreIcon, PencilIcon, TrashIcon } from '../../icons';
import { IAiAgent } from '../../../redux/aiAgents/types';
import { deleteAiAgent, openAiAgentModal, updateAiAgent } from '../../../redux/actions';

import styles from './AiAgent.css';
import { useCheckDevice } from '../../../hooks/useCheckDevice';

export interface IAiAgentProps {
  agent: IAiAgent;
}

export function AiAgent({ agent }: IAiAgentProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const { isDesktop } = useCheckDevice();

  const renderDropdownMore = () => {
    const dropdownOptions: TDropdownOption[] = [
      {
        label: formatMessage({ id: 'ai-agents.agent.edit' }),
        onClick: () => dispatch(openAiAgentModal(agent)),
        Icon: PencilIcon,
        size: 'sm',
      },
      {
        label: agent.isActive
          ? formatMessage({ id: 'ai-agents.agent.deactivate' })
          : formatMessage({ id: 'ai-agents.agent.activate' }),
        onClick: () => dispatch(updateAiAgent({ ...agent, isActive: !agent.isActive })),
        size: 'sm',
      },
      {
        label: formatMessage({ id: 'ai-agents.agent.delete' }),
        onClick: () => dispatch(deleteAiAgent({ id: agent.id })),
        Icon: TrashIcon,
        color: 'red',
        withUpperline: true,
        withConfirmation: true,
        size: 'sm',
      },
    ];

    return (
      <Dropdown
        renderToggle={(isOpen: boolean) => (
          <MoreIcon className={classnames(styles['agent__more'], isOpen && styles['is-active'])} />
        )}
        options={dropdownOptions}
      />
    );
  };

  return (
    <article className={styles['agent']}>
      <figure>
        {agent.photo ? <img src={agent.photo} alt={agent.name} /> : <AIPlusIcon />}
        {!isDesktop && renderDropdownMore()}
      </figure>
      <div className={styles['agent__info']}>
        <div className={styles['agent__name']}>
          <h2 title={agent.name}>{agent.name}</h2>
          <p className={styles['agent__model']}>{agent.modelSlug}</p>
        </div>
        <div className={styles['agent__stat']}>
          <span
            className={classnames(
              styles['agent__status'],
              agent.isActive ? styles['is-active-status'] : styles['is-inactive-status'],
            )}
          >
            {agent.isActive
              ? formatMessage({ id: 'ai-agents.agent.active' })
              : formatMessage({ id: 'ai-agents.agent.inactive' })}
          </span>
        </div>
      </div>
      <div className={styles['agent__setting']}>{isDesktop && renderDropdownMore()}</div>
    </article>
  );
}
