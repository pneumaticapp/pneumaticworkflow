import * as React from 'react';
import { useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import type { TDropdownOption } from '../../UI';
import { WarningPopup } from '../../UI/WarningPopup';
import { PerformerCard } from '../PerformerCard';
import { cloneAIAgent, deleteAIAgent, updateAIAgent } from '../../../redux/ai/slice';
import { getAIAgentsSortedByName } from '../../../redux/selectors/ai';
import { getAgentCloneName } from './utils/getAgentCloneName';
import { EditAIAgentModal } from './EditAIAgentModal';
import { AgentAvatar } from './AgentAvatar';
import type { ITeamAgentProps } from './types';

export function TeamAgent({ agent, providerName }: ITeamAgentProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const agents = useSelector(getAIAgentsSortedByName);

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

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

  const handleToggleActive = (isChecked: boolean) => {
    dispatch(updateAIAgent({ id: agent.id, isActive: isChecked }));
  };

  const handleClone = () => {
    const { name, providerId, model, systemPrompt, photo, isActive } = agent;

    dispatch(
      cloneAIAgent({
        name: getAgentCloneName(
          name,
          formatMessage({ id: 'team.ai-agents.clone-suffix' }),
          agents.map((existingAgent) => existingAgent.name),
        ),
        providerId,
        model,
        systemPrompt,
        photo,
        isActive,
      }),
    );
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
      label: formatMessage({ id: 'team.ai-agents.clone' }),
      onClick: handleClone,
    },
    {
      label: formatMessage({ id: 'team.ai-agents.delete' }),
      onClick: handleOpenDeleteModal,
      color: 'red',
      withUpperline: true,
    },
  ];

  return (
    <>
      <PerformerCard
        avatar={<AgentAvatar name={agent.name} photo={agent.photo} size="md" />}
        name={agent.name}
        nameBadge={agent.isActive ? undefined : formatMessage({ id: 'team.ai-agents.inactive' })}
        description={`${providerName ?? formatMessage({ id: 'team.ai-agents.unknown-provider' })} · ${agent.model}`}
        toggle={{
          label: formatMessage({ id: 'team.ai-agents.active-toggle' }),
          isChecked: agent.isActive,
          onChange: handleToggleActive,
        }}
        options={dropdownOptions}
        data-testid={`ai-agent-${agent.id}`}
      />

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
    </>
  );
}
