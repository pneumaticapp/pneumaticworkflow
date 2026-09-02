import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch } from 'react-redux';

import { IAIAgent } from '../../../types/ai';
import { BaseModal, ModalHeader } from '../../UI/BaseModal';
import { updateAIAgent } from '../../../redux/ai/slice';
import { CreateAIAgentForm } from '../Users/CreateUserModal/CreateAIAgentForm';
import { IAIAgentFormValues } from '../Users/CreateUserModal/types';

import modalStyles from '../Users/CreateUserModal/CreateUserModal.css';

export interface IEditAIAgentModalProps {
  agent: IAIAgent | null;
  onClose(): void;
}

export function EditAIAgentModal({ agent, onClose }: IEditAIAgentModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  if (!agent) {
    return null;
  }

  const initialValues: IAIAgentFormValues = {
    name: agent.name,
    providerId: String(agent.providerId),
    model: agent.model,
    systemPrompt: agent.systemPrompt,
    photo: agent.photo ?? '',
  };

  const handleSubmit = (values: IAIAgentFormValues) => {
    dispatch(
      updateAIAgent({
        id: agent.id,
        name: values.name.trim(),
        providerId: Number(values.providerId),
        model: values.model,
        systemPrompt: values.systemPrompt,
        photo: values.photo || null,
        // Activation is toggled from the card; editing must not flip it.
        isActive: agent.isActive,
      }),
    );
    onClose();
  };

  return (
    <BaseModal
      isOpen
      toggle={onClose}
      className={`${modalStyles['modal__dialog']} ${modalStyles['modal__dialog--ai-agent']}`}
      contentClassName={`${modalStyles['modal__content']} ${modalStyles['modal__content--ai-agent']}`}
    >
      <ModalHeader toggle={onClose} className={modalStyles['modal__header']} titleTag="div">
        <div data-testid="edit-ai-agent-modal-header">
          {formatMessage({ id: 'team.ai-agents.edit-modal-title' })}
        </div>
      </ModalHeader>

      <CreateAIAgentForm
        isActive
        isOpen
        initialValues={initialValues}
        submitLabel={formatMessage({ id: 'team.create-ai-agent-modal.save' })}
        onSubmit={handleSubmit}
      />
    </BaseModal>
  );
}
