import React, { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { BaseModal, ModalHeader } from '../../UI/BaseModal';
import { Tabs } from '../../UI/Tabs';
import { loadAIProviders } from '../../../redux/ai/slice';
import { closeCreatePerformerModal } from '../../../redux/team/slice';
import { getTeamCreatePerformerModalIsOpen } from '../../../redux/selectors/team';
import { CreateAIAgentTab } from './CreateAIAgentTab';
import { CreateUserTab } from './CreateUserTab';
import type { ICreatePerformerModalProps } from './types';
import { ECreatePerformerModalTab } from './types';

import modalStyles from '../PerformerModal.css';

export function CreatePerformerModal({ initialTab = ECreatePerformerModalTab.User }: ICreatePerformerModalProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const isOpen = useSelector(getTeamCreatePerformerModalIsOpen);
  const [activeTab, setActiveTab] = useState(initialTab);
  const [formsKey, setFormsKey] = useState(0);

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      setFormsKey((key) => key + 1);
      dispatch(loadAIProviders());
    }
  }, [dispatch, isOpen, initialTab]);

  useEffect(
    () => () => {
      dispatch(closeCreatePerformerModal());
    },
    [dispatch],
  );

  const handleClose = () => {
    dispatch(closeCreatePerformerModal());
  };

  return (
    <BaseModal
      isOpen={isOpen}
      toggle={handleClose}
      className={modalStyles['performer-modal__dialog']}
      contentClassName={modalStyles['performer-modal__content']}
    >
      <ModalHeader toggle={handleClose} className={modalStyles['performer-modal__header']} titleTag="div">
        <Tabs
          values={[
            { id: ECreatePerformerModalTab.User, label: formatMessage({ id: 'team.create-performer-modal.tab-user' }) },
            {
              id: ECreatePerformerModalTab.AIAgent,
              label: formatMessage({ id: 'team.create-performer-modal.tab-ai-agent' }),
            },
          ]}
          activeValueId={activeTab}
          variant="pill"
          onChange={setActiveTab}
        />
      </ModalHeader>

      <CreateAIAgentTab key={`agent-${formsKey}`} isVisible={activeTab === ECreatePerformerModalTab.AIAgent} />
      <CreateUserTab key={`user-${formsKey}`} isVisible={activeTab === ECreatePerformerModalTab.User} />
    </BaseModal>
  );
}
