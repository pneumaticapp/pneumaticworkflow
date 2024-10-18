import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { TemplateCardFooter } from './TemplateCardFooter';
import {
  ActivityIcon,
  BoxesIcon,
  IntegrateIcon,
  MoreIcon,
  PencilIcon,
  PlayLogoIcon,
  TrashIcon,
  UnionIcon,
} from '../../icons';
import { WarningPopup } from '../../UI/WarningPopup';
import { ETemplateParts, ITemplateListItem } from '../../../types/template';
import { history } from '../../../utils/history';
import { sanitizeText } from '../../../utils/strings';
import { TCloneTemplatePayload, TDeleteTemplatePayload } from '../../../redux/actions';
import { Dropdown, TDropdownOption } from '../../UI';
import { getTemplateEditRoute } from '../../../utils/routes';
import { getLinkToHighlightsByTemplate } from '../../../utils/routes/getLinkToHighlightsByTemplate';
import { getLinkToWorkflows } from '../../../utils/routes/getLinkToWorkflows';
import { getLinkToTemplate } from '../../../utils/routes/getLinkToTemplate';

import styles from '../Templates.css';

export interface ITemplateCardProps extends ITemplateListItem {
  canEdit: boolean | undefined;
  onRunWorkflow(): void;
  cloneTemplate(payload: TCloneTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
}

export interface ITemplateCardState {
  isModalVisible: boolean;
}

export function TemplateCard({
  canEdit,
  id,
  isActive,
  isPublic,
  name,
  tasksCount,
  deleteTemplate,
  cloneTemplate,
  onRunWorkflow,
}: ITemplateCardProps) {
  const { formatMessage } = useIntl();
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);

  const openDeleteTemplateModal = () => {
    setIsDeleteModalVisible(true);
  };

  const closeDeleteTemplateModal = () => {
    setIsDeleteModalVisible(false);
  };

  const handleEditTemplate = () => {
    history.push(getTemplateEditRoute(id));
  };

  const handleShowWorkflows = () => {
    history.push(getLinkToWorkflows({ templateId: id }));
  };

  const handleShowActivity = () => {
    history.push(getLinkToHighlightsByTemplate(id));
  };

  const handleCloneTemplate = () => {
    cloneTemplate({ templateId: id });
  };

  const handleIntegrateTemplate = () => {
    history.push(getLinkToTemplate({ templateId: id, templatePart: ETemplateParts.Integrations }));
  };

  const dropdownOptions: TDropdownOption[] = [
    {
      label: formatMessage({ id: 'templates.run-workflow' }),
      onClick: onRunWorkflow,
      Icon: PlayLogoIcon,
      size: 'sm',
      isHidden: !isActive,
    },
    {
      label: formatMessage({ id: 'workflows.edit-template' }),
      onClick: handleEditTemplate,
      Icon: PencilIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'template.more-show-workflows' }),
      onClick: handleShowWorkflows,
      Icon: BoxesIcon,
      size: 'sm',
      isHidden: !isActive,
    },
    {
      label: formatMessage({ id: 'template.more-show-activity' }),
      onClick: handleShowActivity,
      Icon: ActivityIcon,
      size: 'sm',
      isHidden: !isActive,
    },
    {
      label: formatMessage({ id: 'template.more-clone-template' }),
      onClick: handleCloneTemplate,
      Icon: UnionIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'template.more-integrate-template' }),
      onClick: handleIntegrateTemplate,
      Icon: IntegrateIcon,
      size: 'sm',
    },
    {
      label: formatMessage({ id: 'template.remove' }),
      onClick: openDeleteTemplateModal,
      Icon: TrashIcon,
      color: 'red',
      withUpperline: true,
      size: 'sm',
    },
  ];

  return (
    <div className={styles['card']} key={id}>
      <WarningPopup
        acceptTitle={formatMessage({ id: 'template.remove-accept' })}
        declineTitle={formatMessage({ id: 'template.remove-cancel' })}
        title={formatMessage({ id: 'template.remove-title' })}
        message={formatMessage({ id: 'template.remove-message' }, { template: <b>{name}</b> })}
        closeModal={closeDeleteTemplateModal}
        isOpen={isDeleteModalVisible}
        onConfirm={() => deleteTemplate({ templateId: id })}
        onReject={closeDeleteTemplateModal}
      />
      <div className={styles['card__content']}>
        <div className={styles['card__header']}>
          <Link className={styles['card__title']} key={id} to={getTemplateEditRoute(id)}>
            {sanitizeText(name)}
          </Link>
          {canEdit && (
            <Dropdown
              renderToggle={(isOpen) => (
                <MoreIcon className={classnames(styles['card__more'], isOpen && styles['is-active'])} />
              )}
              options={dropdownOptions}
            />
          )}
        </div>

        <TemplateCardFooter
          templateId={id}
          isActive={isActive}
          isPublic={isPublic}
          tasksCount={tasksCount}
          onRunWorkflow={onRunWorkflow}
        />
      </div>
    </div>
  );
}
