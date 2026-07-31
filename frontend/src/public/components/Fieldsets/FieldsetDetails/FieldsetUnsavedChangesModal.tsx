import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import { Button, RouteLeavingGuard } from '../../UI';
import { getCurrentFieldset } from '../../../redux/selectors/fieldsets';
import { TFieldsetUnsavedChangesModalProps } from './types';

export function FieldsetUnsavedChangesModal({ isChanged }: TFieldsetUnsavedChangesModalProps) {
  const { formatMessage } = useIntl();
  const fieldset = useSelector(getCurrentFieldset);

  if (!fieldset) {
    return null;
  }

  const { id, name } = fieldset;

  return (
    <RouteLeavingGuard
      when={isChanged}
      title={formatMessage({ id: 'fieldsets.leave-unsaved-title' }, { name })}
      message={formatMessage({ id: 'fieldsets.leave-unsaved-message' })}
      onConfirm={(path) => {
        history.push(path);
      }}
      onReject={() => {}}
      shouldBlockNavigation={(location) => {
        const detailPath = ERoutes.FieldsetDetail.replace(':id', String(id));
        return location.pathname !== detailPath;
      }}
      renderControlls={(confirmLeave, stay) => (
        <>
          <Button
            label={formatMessage({ id: 'fieldsets.leave-unsaved-stay' })}
            onClick={stay}
            buttonStyle="transparent-black"
            size="md"
          />
          <Button
            label={formatMessage({ id: 'fieldsets.leave-unsaved-leave' })}
            onClick={confirmLeave}
            buttonStyle="yellow"
            size="md"
          />
        </>
      )}
    />
  );
}
