import React from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { ERoutes } from '../../../constants/routes';
import { checkSomeRouteMatchesLocation, history } from '../../../utils/history';
import { Button, RouteLeavingGuard } from '../../UI';
import { WarningPopup } from '../../UI/WarningPopup';
import { ITemplateNavigationProps } from './types';

import styles from './TemplateControlls.css';

export function TemplateNavigation({
  templateId,
  templateName,
  isActive,
  isDeleted,
  isDeleteModalOpen,
  onCloseDeleteModal,
  onDelete,
  onActivate,
  onDiscard,
}: ITemplateNavigationProps) {
  const { formatMessage } = useIntl();

  return (
    <>
      {templateId && (
        <WarningPopup
          acceptTitle={formatMessage({ id: 'template.remove-accept' })}
          declineTitle={formatMessage({ id: 'template.remove-cancel' })}
          title={formatMessage({ id: 'template.remove-title' })}
          message={formatMessage({ id: 'template.remove-message' }, { template: <strong>{templateName}</strong> })}
          closeModal={onCloseDeleteModal}
          isOpen={isDeleteModalOpen}
          onConfirm={onDelete}
          onReject={onCloseDeleteModal}
        />
      )}

      {templateId && (
        <RouteLeavingGuard
          when={!isActive && !isDeleted}
          title={formatMessage({ id: 'templates.inactive-warning-title' })}
          message={formatMessage({ id: 'templates.inactive-warning-message' })}
          onConfirm={onActivate}
          onReject={(path) => history.push(path)}
          shouldBlockNavigation={({ pathname }) => !checkSomeRouteMatchesLocation(pathname, [
            ERoutes.TemplateView,
            ERoutes.TemplatesEdit,
            ERoutes.TemplatesCreate,
            ERoutes.Login,
          ])}
          renderControlls={(confirm, reject) => (
            <>
              <Button
                label={formatMessage({ id: 'templates.save-and-enable-button' })}
                onClick={confirm}
                buttonStyle="yellow"
                size="md"
              />
              <Button
                label={formatMessage({ id: 'templates.save-as-draft' })}
                onClick={reject}
                buttonStyle="transparent-black"
                size="md"
              />
              <button
                type="button"
                className={classnames('cancel-button', styles['keep-draf-button'])}
                onClick={() => onDiscard(reject)}
              >
                {formatMessage({ id: 'templates.discard-changes' })}
              </button>
            </>
          )}
        />
      )}
    </>
  );
}
