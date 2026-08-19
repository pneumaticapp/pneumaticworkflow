import * as React from 'react';
import { useEffect, useState, useMemo, useCallback, ChangeEvent } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import classNames from 'classnames';

import { validateFieldsetTitle } from '../../../utils/validators';

import {
  openEditModal,
  deleteFieldsetAction,
  cloneFieldsetAction,
  loadCurrentFieldset,
  resetCurrentFieldset,
  updateFieldsetAction,
} from '../../../redux/fieldsets/slice';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button, Tooltip } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { NotificationManager } from '../../UI/Notifications';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { EFieldsetModalType } from '../FieldsetModal/types';
import { FieldsetDetailsSkeleton } from './FieldsetDetailsSkeleton';
import { FieldsetUnsavedChangesModal } from './FieldsetUnsavedChangesModal';

import { getCurrentFieldset, isCurrentFieldsetLoading } from '../../../redux/selectors/fieldsets';
import { getAccountId } from '../../../redux/selectors/user';

import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../types/template';
import { FilledInfoIcon } from '../../icons';
import { EInputNameBackgroundColor, EMoveDirections } from '../../../types/workflow';
import {
  IFieldsetRuleSet,
  EFieldLabelPosition,
  IUpdateFieldsetParams,
} from '../../../types/fieldset';
import { ExtraFieldsMap } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../../TemplateEdit/ExtraFields';
import { getEmptyField } from '../../TemplateEdit/KickoffRedux/utils/getEmptyField';
import { getEditedFields } from '../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../utils/workflows';
import { useDatasetOptions } from '../../TemplateEdit/ExtraFields/utils/useDatasetOptions';

import { normalizeFieldsForUI } from './fieldsetFieldMappers';
import { validateFieldsetRules } from '../validators';
import { FIELDSET_LABEL_POSITION_OPTIONS } from '../constants';

import { useCheckDevice } from '../../../hooks/useCheckDevice';

import { TFieldsetDetailsProps, TLocalFieldsetState, TFieldsetChanges } from './types';
import { FieldsetRulesets } from './FieldsetRulesets/FieldsetRulesets';
import styles from './FieldsetDetails.css';


const EMPTY_LOCAL_FIELDSET: TLocalFieldsetState = {
  title: '',
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  fields: [],
  rulesets: [],
};

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
  const { isDesktop } = useCheckDevice();

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

  useEffect(() => {
    return () => {
      dispatch(resetCurrentFieldset());
    };
  }, []);

  useEffect(() => {
    if (!fieldset) return;

    setLocalFieldset({
      title: fieldset.title,
      description: fieldset.description || '',
      labelPosition: fieldset.labelPosition,
      fields: normalizeFieldsForUI(fieldset.fields as unknown as IExtraField[]),
      rulesets: fieldset.rulesets || [],
    });
    setFieldsetChanges({});
  }, [fieldset?.id, fieldset?.title, fieldset?.description, fieldset?.labelPosition, fieldset?.fields, fieldset?.rulesets]);

  const handleSettingsTitleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const title = event.target.value;
    setLocalFieldset((prev) => ({ ...prev, title }));
    setFieldsetChanges((prev) => ({ ...prev, title }));
  };

  const handleSettingsDescriptionChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const description = event.target.value;
    setLocalFieldset((prev) => ({ ...prev, description }));
    setFieldsetChanges((prev) => ({ ...prev, description }));
  };

  const handleSettingsLabelPositionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const labelPosition = event.target.value as EFieldLabelPosition;
    setLocalFieldset((prev) => ({ ...prev, labelPosition }));
    setFieldsetChanges((prev) => ({ ...prev, labelPosition }));
  };

  const getSortedFields = useCallback(() => {
    return [...localFieldset.fields].sort((a, b) => b.order - a.order);
  }, [localFieldset.fields]);

  const sortedFields = useMemo(() => getSortedFields(), [getSortedFields]);

  const handleCreateField = (type: EExtraFieldType) => {
    const newFields = getNormalizeFieldsOrders([...localFieldset.fields, getEmptyField(type, formatMessage)]);
    setLocalFieldset((prev) => ({ ...prev, fields: newFields }));
    setFieldsetChanges((prev) => ({ ...prev, fields: newFields }));
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const newFields = getEditedFields(getSortedFields(), apiName, changedProps);
    setLocalFieldset((prev) => ({ ...prev, fields: newFields }));
    setFieldsetChanges((prev) => ({ ...prev, fields: newFields }));
  };

  const handleDeleteField = (idx: number) => {
    const newFields = getNormalizeFieldsOrders(getSortedFields().filter((_, index) => index !== idx));
    setLocalFieldset((prev) => ({ ...prev, fields: newFields }));
    setFieldsetChanges((prev) => ({ ...prev, fields: newFields }));
  };

  const handleMoveField = (from: number, direction: EMoveDirections) => {
    const to = direction === EMoveDirections.Up ? from - 1 : from + 1;
    const newFields = moveWorkflowField(from, to, getSortedFields());
    setLocalFieldset((prev) => ({ ...prev, fields: newFields }));
    setFieldsetChanges((prev) => ({ ...prev, fields: newFields }));
  };

  const handleRulesetsChange = (rulesets: IFieldsetRuleSet[]) => {
    setLocalFieldset((prev) => ({ ...prev, rulesets }));
    setFieldsetChanges((prev) => ({ ...prev, rulesets }));
  };

  const handleSave = () => {
    if (!fieldset || !isChanged) return;

    const titleErrorMessageKey = validateFieldsetTitle(localFieldset.title);

    if (titleErrorMessageKey) {
      NotificationManager.warning({
        message: formatMessage({ id: titleErrorMessageKey }),
      });
      return;
    }

    if (fieldsetChanges.rulesets) {
      const ruleErrorMessageKey = validateFieldsetRules(fieldsetChanges.rulesets, localFieldset.fields);

      if (ruleErrorMessageKey) {
        NotificationManager.warning({
          message: formatMessage({ id: ruleErrorMessageKey }),
        });
        return;
      }
    }

    const payload: IUpdateFieldsetParams = {
      id: fieldset.id,
    };

    if (fieldsetChanges.title !== undefined) {
      payload.title = fieldsetChanges.title;
    }
    if (fieldsetChanges.description !== undefined) {
      payload.description = fieldsetChanges.description;
    }
    if (fieldsetChanges.labelPosition) {
      payload.labelPosition = fieldsetChanges.labelPosition;
    }
    if (fieldsetChanges.fields) {
      payload.fields = fieldsetChanges.fields.map(
        ({ id: _id, ...rest }) => rest,
      ) as IUpdateFieldsetParams['fields'];
    }
    if (fieldsetChanges.rulesets) {
      payload.rulesets = fieldsetChanges.rulesets;
    }

    dispatch(updateFieldsetAction(payload));
  };


  if (isLoading) {
    return <FieldsetDetailsSkeleton />;
  }

  if (!fieldset) {
    return null;
  }

  const handleCloneFieldset = () => {
    if (isChanged) {
      NotificationManager.warning({
        message: formatMessage({ id: 'fieldsets.clone-unsaved-warning' }),
      });
      return;
    }
    dispatch(cloneFieldsetAction({ id: fieldset.id }));
  };

  return (
    <div className={styles['container']}>
      <FieldsetUnsavedChangesModal isChanged={isChanged} />

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
            onClone={handleCloneFieldset}
            editLabel={formatMessage({ id: 'fieldsets.edit' })}
            deleteLabel={formatMessage({ id: 'fieldsets.delete' })}
            cloneLabel={formatMessage({ id: 'fieldsets.clone' })}
            toggleType={EModifyDropdownToggle.Modify}
          />
        </div>
      </header>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>{formatMessage({ id: 'fieldsets.settings-section' })}</h2>

        <div className={styles['settings-form']}>
          <div className={styles['settings-field']}>
            <label htmlFor="fieldset-title" className={styles['settings-label']}>
              {formatMessage({ id: 'fieldsets.settings.title' })}
              <Tooltip
                content={formatMessage({ id: 'fieldsets.settings.title-tooltip' })}
                placement="top"
              >
                <span>
                  <FilledInfoIcon />
                </span>
              </Tooltip>
            </label>
            <input
              id="fieldset-title"
              type="text"
              className={classNames(
                styles['settings-input'],
                Boolean(validateFieldsetTitle(localFieldset.title)) && styles['settings-input_error'],
              )}
              value={localFieldset.title}
              placeholder={formatMessage({ id: 'fieldsets.settings.title-placeholder' })}
              onChange={handleSettingsTitleChange}
            />
          </div>

          <div className={styles['settings-field']}>
            <label htmlFor="fieldset-description" className={styles['settings-label']}>
              {formatMessage({ id: 'fieldsets.settings.description' })}
              <Tooltip
                content={formatMessage({ id: 'fieldsets.settings.description-tooltip' })}
                placement="top"
              >
                <span className={styles['settings-info-icon']}>
                  <FilledInfoIcon />
                </span>
              </Tooltip>
            </label>
            <textarea
              id="fieldset-description"
              className={styles['settings-textarea']}
              value={localFieldset.description}
              placeholder={formatMessage({ id: 'fieldsets.settings.description-placeholder' })}
              onChange={handleSettingsDescriptionChange}
            />
          </div>

          <div className={styles['settings-field']}>
            <label htmlFor="fieldset-label-position" className={styles['settings-label']}>
              {formatMessage({ id: 'fieldsets.settings.label-position' })}
            </label>
            <select
              id="fieldset-label-position"
              className={styles['settings-select']}
              value={localFieldset.labelPosition}
              onChange={handleSettingsLabelPositionChange}
            >
              {FIELDSET_LABEL_POSITION_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {formatMessage({ id: option.labelKey })}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>{formatMessage({ id: 'fieldsets.fields-section' })}</h2>

        <div className={styles['components']}>
          {ExtraFieldsMap.map((x) => (
            <ExtraFieldIcon {...x} key={x.id} onClick={() => handleCreateField(x.id)} />
          ))}
        </div>

        {sortedFields.length > 0 && (
          <div className={styles['fields']}>
            {sortedFields.map((field, index) => (
              <ExtraFieldIntl
                key={field.apiName}
                id={index}
                field={field}
                fieldsCount={sortedFields.length}
                labelBackgroundColor={EInputNameBackgroundColor.White}
                deleteField={() => handleDeleteField(index)}
                moveFieldUp={() => handleMoveField(index, EMoveDirections.Up)}
                moveFieldDown={() => handleMoveField(index, EMoveDirections.Down)}
                editField={handleEditField(field.apiName)}
                accountId={accountId}
                mode={EExtraFieldMode.Kickoff}
                showDropdown
                datasetOptions={datasetOptions}
                labelPosition={isDesktop ? localFieldset.labelPosition : EFieldLabelPosition.Top}
              />
            ))}
          </div>
        )}

        {sortedFields.length === 0 && (
          <p className={styles['empty-text']}>{formatMessage({ id: 'fieldsets.no-fields' })}</p>
        )}
      </div>

      <FieldsetRulesets
        rulesets={localFieldset.rulesets}
        fields={localFieldset.fields}
        onRulesetsChange={handleRulesetsChange}
      />

      <div className={styles['save-bar']}>
        <Button
          label={formatMessage({ id: 'fieldsets.save' })}
          buttonStyle="yellow"
          size="md"
          onClick={handleSave}
          disabled={!isChanged}
        />
        {isChanged && (
          <span className={styles['save-bar__hint']}>{formatMessage({ id: 'fieldsets.unsaved-changes' })}</span>
        )}
      </div>

      <FieldsetModal type={EFieldsetModalType.Edit} />
    </div>
  );
};

export default FieldsetDetails;
