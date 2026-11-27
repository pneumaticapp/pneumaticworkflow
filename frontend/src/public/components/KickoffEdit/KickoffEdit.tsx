import React, { useEffect, useMemo, useRef } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import type { IExtraField, IRuntimeKickoffClient } from '../../types/template';
import type { IFieldsetRuntime } from '../../types/fieldset';
import { EInputNameBackgroundColor } from '../../types/workflow';
import { isArrayWithItems } from '../../utils/helpers';
import { IntlMessages } from '../IntlMessages';
import { checkExtraFieldsAreValid } from '../WorkflowEditPopup/utils/areKickoffFieldsValid';
import { Loader } from '../UI/Loader';
import { autoFocusFirstField } from '../../utils/autoFocusFirstField';
import { getVisibleFieldsByShowRules } from '../../utils/fieldShowVisibility';
import { MergedOutputList } from '../MergedOutputList';

import { Button } from '../UI/Buttons/Button';

import styles from './KickoffEdit.css';

export interface IEditKickoffProps {
  kickoff: IRuntimeKickoffClient | null;
  fieldsets?: IFieldsetRuntime[];
  isLoading?: boolean;
  accountId: number;
  onEditField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  onEditFieldsetField?(apiName: string): (changedProps: Partial<IExtraField>) => void;
  onSave?(): void;
  onCancel?(): void;
}

export function EditKickoff({
  kickoff,
  fieldsets = [],
  isLoading = false,
  accountId,
  onEditField,
  onEditFieldsetField,
  onSave,
  onCancel,
}: IEditKickoffProps) {
  const { formatMessage } = useIntl();
  const wrapperRef = useRef<HTMLFormElement>(null);
  const hasKickoffContent = Boolean(kickoff && (isArrayWithItems(kickoff.fields) || isArrayWithItems(fieldsets)));

  const { visibleFields, visibleFieldsets } = useMemo(
    () => getVisibleFieldsByShowRules(kickoff?.fields || [], fieldsets),
    [kickoff?.fields, fieldsets],
  );

  useEffect(() => {
    if (hasKickoffContent) {
      autoFocusFirstField(wrapperRef.current);
    }
  }, [hasKickoffContent]);

  if (!hasKickoffContent || !kickoff) return null;

  const renderButtons = () => {
    if (!onSave && !onCancel) return null;

    return (
      <div className={styles['kickoff-buttons']}>
        {Boolean(onSave) && (
          <Button
            type="submit"
            disabled={
              !checkExtraFieldsAreValid(visibleFields) ||
              visibleFieldsets.some((fieldset) => !checkExtraFieldsAreValid(fieldset.fields))
            }
            label={formatMessage({ id: 'kickoff-edit.buttons.save' })}
            buttonStyle="yellow"
          />
        )}

        {Boolean(onCancel) && (
          <Button
            type="button"
            className={classnames('cancel-button', styles['kickoff-buttons__cancel'])}
            onClick={onCancel}
            label={formatMessage({ id: 'kickoff-edit.buttons.cancel' })}
          />
        )}
      </div>
    );
  };

  const renderKickoffFields = () => {
    return (
      <>
        <p className={styles['kickoff__title']}>
          <IntlMessages id="template.kick-off-form-title" />
        </p>
        {kickoff.description && <p className={styles['kickoff__description']}>{kickoff.description}</p>}
        <div className={styles['kickoff__inputs']}>
          <MergedOutputList
            fields={visibleFields}
            fieldsets={visibleFieldsets}
            onEditField={onEditField}
            onEditFieldsetField={onEditFieldsetField || onEditField}
            labelBackgroundColor={EInputNameBackgroundColor.White}
            fieldClassName={styles['kickoff__field']}
            accountId={accountId}
          />
        </div>

        {renderButtons()}
      </>
    );
  };

  const handleSubmit = (e: React.SyntheticEvent) => {
    e.preventDefault();

    onSave!();
  };

  return onSave ? (
    <form ref={wrapperRef} className={styles['container']} onSubmit={handleSubmit}>
      <Loader isLoading={isLoading} />
      {renderKickoffFields()}
    </form>
  ) : (
    <div className={styles['container']}>{renderKickoffFields()}</div>
  );
}
