import React, { useEffect } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { IExtraField, EExtraFieldMode, IKickoff, IFieldsetData } from '../../types/template';
import { EInputNameBackgroundColor } from '../../types/workflow';
import { isArrayWithItems } from '../../utils/helpers';
import { IntlMessages } from '../IntlMessages';
import { ExtraFieldIntl } from '../TemplateEdit/ExtraFields';
import { FieldsetFieldGroup } from '../FieldsetFieldGroup';
import { checkExtraFieldsAreValid } from '../WorkflowEditPopup/utils/areKickoffFieldsValid';
import { Loader } from '../UI/Loader';
import { autoFocusFirstField } from '../../utils/autoFocusFirstField';

import { Button } from '../UI/Buttons/Button';

import styles from './KickoffEdit.css';

export interface IEditKickoffProps {
  kickoff: IKickoff | null;
  fieldsets?: IFieldsetData[];
  isLoading?: boolean;
  accountId: number;
  onEditField(apiName: string): (changedProps: Partial<IExtraField>) => void;
  onSave?(): void;
  onCancel?(): void;
}

export function EditKickoff({
  kickoff,
  fieldsets = [],
  isLoading = false,
  accountId,
  onEditField,
  onSave,
  onCancel,
}: IEditKickoffProps) {
  if (!kickoff || (!isArrayWithItems(kickoff.fields) && !isArrayWithItems(fieldsets))) return null;

  const { formatMessage } = useIntl();
  const wrapperRef = React.useRef<HTMLFormElement>(null);

  useEffect(() => {
    autoFocusFirstField(wrapperRef.current);
  }, []);

  const renderButtons = () => {
    if (!onSave && !onCancel) return null;

    return (
      <div className={styles['kickoff-buttons']}>
        {Boolean(onSave) && (
          <Button
            type="submit"
            disabled={!checkExtraFieldsAreValid(kickoff.fields)}
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
          {kickoff.fields.map((field) => (
            <ExtraFieldIntl
              key={field.apiName}
              field={{ ...field }}
              editField={onEditField(field.apiName)}
              showDropdown={false}
              mode={EExtraFieldMode.ProcessRun}
              labelBackgroundColor={EInputNameBackgroundColor.White}
              namePlaceholder={field.name}
              descriptionPlaceholder={field.description}
              wrapperClassName={styles['kickoff__field']}
              accountId={accountId}
            />
          ))}
          {fieldsets.map((fs) => (
            <FieldsetFieldGroup
              key={fs.id}
              fields={fs.fields}
              onEditField={onEditField}
              mode={EExtraFieldMode.ProcessRun}
              labelBackgroundColor={EInputNameBackgroundColor.White}
              accountId={accountId}
              fieldClassName={styles['kickoff__field']}
            />
          ))}
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

