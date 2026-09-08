import * as React from 'react';
import { useEffect, useState } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  openEditModal,
  deleteFieldsetAction,
  loadCurrentFieldset,
  resetCurrentFieldset,
} from '../../../redux/fieldsets/slice';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { EFieldsetModalType } from '../FieldsetModal/types';
import { FieldsetDetailsSkeleton } from './FieldsetDetailsSkeleton';
import { FieldsetUnsavedChangesModal } from './FieldsetUnsavedChangesModal';

import { getCurrentFieldset, isCurrentFieldsetLoading } from '../../../redux/selectors/fieldsets';
import { getAccountId } from '../../../redux/selectors/user';

import { IExtraField } from '../../../types/template';
import { useDatasetOptions } from '../../TemplateEdit/ExtraFields/utils/useDatasetOptions';

import { EMPTY_LOCAL_FIELDSET } from './constants';
import {
  initLocalFieldset,
  checkIsTitleError,
  updateFieldsetProperty,
  saveFieldset,
  cloneFieldset,
} from './utils';

import { TFieldsetDetailsProps, TLocalFieldsetState, TFieldsetChanges } from './types';
import { FieldsetRulesetsList } from './FieldsetRulesetsList/FieldsetRulesetsList';
import { FieldsetFieldsList } from './FieldsetFieldsList/FieldsetFieldsList';
import { FieldRuleModal } from './FieldRuleModal';
import { FieldsetUsageBanner } from './FieldsetUsageBanner/FieldsetUsageBanner';
import { FieldsetSettings } from './FieldsetSettings/FieldsetSettings';
import { useFieldRuleModal } from './useFieldRuleModal';

import styles from './FieldsetDetails.css';

const FieldsetDetails = ({
  match: {
    params: { id: matchParamId },
  },
}: TFieldsetDetailsProps) => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const fieldset = useSelector(getCurrentFieldset);
  const isLoading = useSelector(isCurrentFieldsetLoading);
  const accountId = useSelector(getAccountId);

  const [localFieldset, setLocalFieldset] = useState<TLocalFieldsetState>(EMPTY_LOCAL_FIELDSET);
  const [fieldsetChanges, setFieldsetChanges] = useState<TFieldsetChanges>({});
  const datasetOptions = useDatasetOptions(localFieldset.fields);

  const fieldsetListRoute = ERoutes.Fieldsets;
  const isChanged = Object.keys(fieldsetChanges).length > 0;

  useEffect(() => {
    const id = Number(matchParamId);

    if (Number.isNaN(id)) {
      history.push(fieldsetListRoute);
      return;
    }

    if (fieldset?.id === id) return;
    dispatch(loadCurrentFieldset({ id }));
  }, [matchParamId]);

  useEffect(() => () => {
    dispatch(resetCurrentFieldset());
  }, []);

  useEffect(() => {
    if (!fieldset) return;

    setLocalFieldset(initLocalFieldset(fieldset));
    setFieldsetChanges({});
  }, [fieldset?.id, fieldset?.title, fieldset?.description, fieldset?.labelPosition, fieldset?.fields, fieldset?.rulesets]);

  const handleFieldsChange = (newFields: IExtraField[]) => {
    updateFieldsetProperty('fields', newFields, setLocalFieldset, setFieldsetChanges);
  };

  const { openFieldRule, handleDeleteFieldRuleset, fieldRuleModalProps } = useFieldRuleModal(
    localFieldset.fields,
    handleFieldsChange,
  );

  const isTitleError = checkIsTitleError(localFieldset.title, fieldsetChanges.title !== undefined);

  if (isLoading) {
    return <FieldsetDetailsSkeleton />;
  }

  if (!fieldset) {
    return null;
  }

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
                })
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
        onTitleChange={(event) =>
          updateFieldsetProperty('title', event.target.value, setLocalFieldset, setFieldsetChanges)
        }
        onDescriptionChange={(event) =>
          updateFieldsetProperty('description', event.target.value, setLocalFieldset, setFieldsetChanges)
        }
        onLabelPositionChange={(key) =>
          updateFieldsetProperty('labelPosition', key, setLocalFieldset, setFieldsetChanges)
        }
      />

      <FieldsetFieldsList
        fields={localFieldset.fields}
        onFieldsChange={handleFieldsChange}
        isReadOnly={isLinked}
        labelPosition={localFieldset.labelPosition}
        accountId={accountId}
        datasetOptions={datasetOptions}
        rulesets={localFieldset.rulesets}
        onRulesetsChange={(rulesets) =>
          updateFieldsetProperty('rulesets', rulesets, setLocalFieldset, setFieldsetChanges)
        }
        onOpenFieldRule={openFieldRule}
        onDeleteFieldRuleset={handleDeleteFieldRuleset}
      />

      <FieldsetRulesetsList
        rulesets={localFieldset.rulesets}
        fields={localFieldset.fields}
        onRulesetsChange={(rulesets) =>
          updateFieldsetProperty('rulesets', rulesets, setLocalFieldset, setFieldsetChanges)
        }
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
        <FieldRuleModal
          {...fieldRuleModalProps}
          fieldType={fieldRuleModalProps.fieldType}
        />
      )}

      <FieldsetModal type={EFieldsetModalType.Edit} />
    </div>
  );
};

export default FieldsetDetails;
