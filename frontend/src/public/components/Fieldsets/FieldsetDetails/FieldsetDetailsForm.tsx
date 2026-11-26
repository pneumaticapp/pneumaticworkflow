import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import { openEditModal, deleteFieldsetAction } from '../../../redux/fieldsets/slice';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { EFieldsetModalType } from '../FieldsetModal/types';
import { FieldsetUnsavedChangesModal } from './FieldsetUnsavedChangesModal';

import { getAccountId } from '../../../redux/selectors/user';

import type { IExtraField } from '../../../types/template';
import { useDatasetOptions } from '../../TemplateEdit/ExtraFields/utils/useDatasetOptions';

import { initLocalFieldset, checkIsTitleError, getFieldsetChanges, saveFieldset, cloneFieldset } from './utils';

import type { TFieldsetDetailsFormProps, TLocalFieldsetState } from './types';
import { FieldsetRulesetsList } from './FieldsetRulesetsList/FieldsetRulesetsList';
import { FieldsetFieldsList } from './FieldsetFieldsList/FieldsetFieldsList';
import { FieldRuleModal } from './FieldRuleModal';
import { FieldsetUsageBanner } from './FieldsetUsageBanner/FieldsetUsageBanner';
import { FieldsetSettings } from './FieldsetSettings/FieldsetSettings';
import { useFieldRuleModal } from './useFieldRuleModal';

import styles from './FieldsetDetails.css';

export function FieldsetDetailsForm({ fieldset }: TFieldsetDetailsFormProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const accountId = useSelector(getAccountId);

  const initialFieldset = useMemo(() => initLocalFieldset(fieldset), [fieldset]);
  const [localFieldset, setLocalFieldset] = useState<TLocalFieldsetState>(initialFieldset);

  useEffect(() => {
    setLocalFieldset(initialFieldset);
  }, [initialFieldset]);

  const fieldsetChanges = useMemo(
    () => getFieldsetChanges(initialFieldset, localFieldset),
    [initialFieldset, localFieldset],
  );
  const datasetOptions = useDatasetOptions(localFieldset.fields);

  const fieldsetListRoute = ERoutes.Fieldsets;
  const isChanged = Object.keys(fieldsetChanges).length > 0;

  const updateFieldset = useCallback(<K extends keyof TLocalFieldsetState>(key: K, value: TLocalFieldsetState[K]) => {
    setLocalFieldset((previousFieldset) => ({ ...previousFieldset, [key]: value }));
  }, []);

  const handleFieldsChange = useCallback(
    (newFields: IExtraField[]) => {
      updateFieldset('fields', newFields);
    },
    [updateFieldset],
  );

  const { openFieldRule, handleDeleteFieldRuleset, fieldRuleModalProps } = useFieldRuleModal(
    localFieldset.fields,
    handleFieldsChange,
  );

  const isTitleError = checkIsTitleError(localFieldset.title, fieldsetChanges.title !== undefined);
  const isLinked = fieldset.usage.length > 0;

  return (
    <div className={styles['container']}>
      <FieldsetUnsavedChangesModal
        isChanged={isChanged}
        onSave={(onSuccess) =>
          saveFieldset({
            fieldset,
            isChanged,
            localFieldset,
            fieldsetChanges,
            dispatch,
            formatMessage,
            onSuccess,
          })
        }
      />

      <header className={styles['header']}>
        <h1 title={fieldset.name}>{fieldset.name}</h1>
        <div className={styles['header__config']}>
          <ModifyDropdown
            onEdit={() => dispatch(openEditModal())}
            onDelete={() => {
              dispatch(
                deleteFieldsetAction({
                  id: fieldset.id,
                  onSuccess: () => {
                    history.push(fieldsetListRoute);
                  },
                }),
              );
            }}
            onClone={() =>
              cloneFieldset({
                fieldsetId: fieldset.id,
                isChanged,
                dispatch,
                formatMessage,
              })
            }
            editLabel={formatMessage({ id: 'fieldsets.edit' })}
            deleteLabel={formatMessage({ id: 'fieldsets.delete' })}
            cloneLabel={formatMessage({ id: 'fieldsets.clone' })}
            isReadOnly={isLinked}
            toggleType={EModifyDropdownToggle.Modify}
          />
        </div>
      </header>

      <FieldsetUsageBanner usage={fieldset.usage} />

      <FieldsetSettings
        title={localFieldset.title}
        description={localFieldset.description}
        labelPosition={localFieldset.labelPosition}
        isReadOnly={isLinked}
        isTitleError={isTitleError}
        onTitleChange={(event) => updateFieldset('title', event.target.value)}
        onDescriptionChange={(event) => updateFieldset('description', event.target.value)}
        onLabelPositionChange={(key) => updateFieldset('labelPosition', key)}
      />

      <FieldsetFieldsList
        fields={localFieldset.fields}
        onFieldsChange={handleFieldsChange}
        isReadOnly={isLinked}
        labelPosition={localFieldset.labelPosition}
        accountId={accountId}
        datasetOptions={datasetOptions}
        rulesets={localFieldset.rulesets}
        onRulesetsChange={(rulesets) => updateFieldset('rulesets', rulesets)}
        onOpenFieldRule={openFieldRule}
        onDeleteFieldRuleset={handleDeleteFieldRuleset}
      />

      <FieldsetRulesetsList
        rulesets={localFieldset.rulesets}
        fields={localFieldset.fields}
        onRulesetsChange={(rulesets) => updateFieldset('rulesets', rulesets)}
        isReadOnly={isLinked}
      />

      {!isLinked && (
        <div className={styles['save-bar']}>
          <Button
            label={formatMessage({ id: 'fieldsets.save' })}
            buttonStyle="yellow"
            size="md"
            onClick={() =>
              saveFieldset({
                fieldset,
                isChanged,
                localFieldset,
                fieldsetChanges,
                dispatch,
                formatMessage,
              })
            }
            disabled={!isChanged}
          />
          {isChanged && (
            <span className={styles['save-bar__hint']}>{formatMessage({ id: 'fieldsets.unsaved-changes' })}</span>
          )}
        </div>
      )}

      {fieldRuleModalProps.fieldType && (
        <FieldRuleModal {...fieldRuleModalProps} fieldType={fieldRuleModalProps.fieldType} />
      )}

      <FieldsetModal type={EFieldsetModalType.Edit} />
    </div>
  );
}
