import * as React from 'react';
import { useEffect, useState, useMemo, useCallback, ChangeEvent } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  openEditModal,
  deleteFieldsetAction,
  loadCurrentFieldset,
  resetCurrentFieldset,
  updateFieldsetAction,
} from '../../../redux/fieldsets/slice';

import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button, FilterSelect } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { NotificationManager } from '../../UI/Notifications';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { EFieldsetModalType } from '../FieldsetModal/types';
import { FieldsetDetailsSkeleton } from './FieldsetDetailsSkeleton';
import { FieldsetUnsavedChangesModal } from './FieldsetUnsavedChangesModal';

import { getCurrentFieldset, isCurrentFieldsetLoading } from '../../../redux/selectors/fieldsets';
import { getAccountId } from '../../../redux/selectors/user';

import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../types/template';
import { EInputNameBackgroundColor, EMoveDirections } from '../../../types/workflow';
import {
  IFieldsetTemplateRule,
  EFieldLabelPosition,
  EFieldsetRuleType,
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
import {
  FIELDSET_LABEL_POSITION_OPTIONS,
  FIELDSET_RULE_TYPES,
  FIELDSET_RULE_VALUE_PLACEHOLDER_BY_TYPE,
} from '../constants';

import { useCheckDevice } from '../../../hooks/useCheckDevice';

import { TFieldsetDetailsProps, TDetailFieldsetState, TDetailFieldsetChanges } from './types';
import styles from './FieldsetDetails.css';

const EMPTY_DETAIL_FIELDSET: TDetailFieldsetState = {
  description: '',
  labelPosition: EFieldLabelPosition.Top,
  fields: [],
  rules: [],
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

  const [detailFieldset, setDetailFieldset] = useState<TDetailFieldsetState>(EMPTY_DETAIL_FIELDSET);
  const [detailFieldsetChanges, setDetailFieldsetChanges] = useState<TDetailFieldsetChanges>({});
  const datasetOptions = useDatasetOptions(detailFieldset.fields);

  const fieldsetListRoute = ERoutes.Fieldsets;
  const isChanged = Object.keys(detailFieldsetChanges).length > 0;

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

    setDetailFieldset({
      description: fieldset.description || '',
      labelPosition: fieldset.labelPosition,
      fields: normalizeFieldsForUI(fieldset.fields as unknown as IExtraField[]),
      rules: fieldset.rules || [],
    });
    setDetailFieldsetChanges({});
  }, [fieldset?.id, fieldset?.description, fieldset?.labelPosition, fieldset?.fields, fieldset?.rules]);
  const handleSettingsDescriptionChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const description = event.target.value;
    setDetailFieldset((prev) => ({ ...prev, description }));
    setDetailFieldsetChanges((prev) => ({ ...prev, description }));
  };

  const handleSettingsLabelPositionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const labelPosition = event.target.value as EFieldLabelPosition;
    setDetailFieldset((prev) => ({ ...prev, labelPosition }));
    setDetailFieldsetChanges((prev) => ({ ...prev, labelPosition }));
  };

  const getSortedFields = useCallback(() => {
    return [...detailFieldset.fields].sort((a, b) => b.order - a.order);
  }, [detailFieldset.fields]);

  const sortedFields = useMemo(() => getSortedFields(), [getSortedFields]);

  const handleCreateField = (type: EExtraFieldType) => {
    const newFields = getNormalizeFieldsOrders([...detailFieldset.fields, getEmptyField(type, formatMessage)]);
    setDetailFieldset((prev) => ({ ...prev, fields: newFields }));
    setDetailFieldsetChanges((prev) => ({ ...prev, fields: newFields }));
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const newFields = getEditedFields(getSortedFields(), apiName, changedProps);
    setDetailFieldset((prev) => ({ ...prev, fields: newFields }));
    setDetailFieldsetChanges((prev) => ({ ...prev, fields: newFields }));
  };

  const handleDeleteField = (idx: number) => {
    const newFields = getNormalizeFieldsOrders(getSortedFields().filter((_, index) => index !== idx));
    setDetailFieldset((prev) => ({ ...prev, fields: newFields }));
    setDetailFieldsetChanges((prev) => ({ ...prev, fields: newFields }));
  };

  const handleMoveField = (from: number, direction: EMoveDirections) => {
    const to = direction === EMoveDirections.Up ? from - 1 : from + 1;
    const newFields = moveWorkflowField(from, to, getSortedFields());
    setDetailFieldset((prev) => ({ ...prev, fields: newFields }));
    setDetailFieldsetChanges((prev) => ({ ...prev, fields: newFields }));
  };

  const handleAddRule = () => {
    const newRule: IFieldsetTemplateRule = {
      apiName: `temporary-${Date.now()}`,
      type: FIELDSET_RULE_TYPES[0].value,
      value: '',
      fields: [],
    };
    const rules = [...detailFieldset.rules, newRule];
    setDetailFieldset((prev) => ({ ...prev, rules }));
    setDetailFieldsetChanges((prev) => ({ ...prev, rules }));
  };

  const handleEditRuleValue = (index: number, value: string) => {
    const rules = detailFieldset.rules.map((rule, i) => (i === index ? { ...rule, value } : rule));
    setDetailFieldset((prev) => ({ ...prev, rules }));
    setDetailFieldsetChanges((prev) => ({ ...prev, rules }));
  };

  const handleEditRuleType = (index: number, type: EFieldsetRuleType) => {
    const rules = detailFieldset.rules.map((rule, i) => (i === index ? { ...rule, type } : rule));
    setDetailFieldset((prev) => ({ ...prev, rules }));
    setDetailFieldsetChanges((prev) => ({ ...prev, rules }));
  };

  const handleEditRuleFields = (index: number, fieldApiNames: (string | number | null)[]) => {
    const rules = detailFieldset.rules.map((rule, i) =>
      i === index
        ? { ...rule, fields: fieldApiNames.filter((name): name is string => typeof name === 'string') }
        : rule,
    );
    setDetailFieldset((prev) => ({ ...prev, rules }));
    setDetailFieldsetChanges((prev) => ({ ...prev, rules }));
  };

  const handleDeleteRule = (index: number) => {
    const rules = detailFieldset.rules.filter((_, i) => i !== index);
    setDetailFieldset((prev) => ({ ...prev, rules }));
    setDetailFieldsetChanges((prev) => ({ ...prev, rules }));
  };

  const handleSave = () => {
    if (!fieldset || !isChanged) return;

    if (detailFieldsetChanges.rules) {
      const ruleErrorMessageKey = validateFieldsetRules(detailFieldsetChanges.rules, detailFieldset.fields);

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

    if (detailFieldsetChanges.description) {
      payload.description = detailFieldsetChanges.description;
    }
    if (detailFieldsetChanges.labelPosition) {
      payload.labelPosition = detailFieldsetChanges.labelPosition;
    }
    if (detailFieldsetChanges.fields) {
      payload.fields = detailFieldsetChanges.fields.map(
        ({ id: _id, ...rest }) => rest,
      ) as IUpdateFieldsetParams['fields'];
    }
    if (detailFieldsetChanges.rules) {
      payload.rules = detailFieldsetChanges.rules.map(({ apiName, ...rule }) => ({
        ...rule,
        ...(apiName.startsWith('temporary-') ? {} : { apiName }),
      })) as IFieldsetTemplateRule[];
    }

    dispatch(updateFieldsetAction(payload));
  };

  const getRuleValuePlaceholder = (ruleType: EFieldsetRuleType) =>
    formatMessage({ id: FIELDSET_RULE_VALUE_PLACEHOLDER_BY_TYPE[ruleType] });

  if (isLoading) {
    return <FieldsetDetailsSkeleton />;
  }

  if (!fieldset) {
    return null;
  }

  return (
    <div className={styles['container']}>
      <FieldsetUnsavedChangesModal isChanged={isChanged} />

      <header className={styles['header']}>
        <h1 title={fieldset.name}>{fieldset.name}</h1>
        <div className={styles['header__config']}>
          <ModifyDropdown
            onEdit={() => dispatch(openEditModal())}
            onDelete={() => {
              dispatch(deleteFieldsetAction({ id: fieldset.id }));
              history.push(fieldsetListRoute);
            }}
            editLabel={formatMessage({ id: 'fieldsets.edit' })}
            deleteLabel={formatMessage({ id: 'fieldsets.delete' })}
            toggleType={EModifyDropdownToggle.Modify}
          />
        </div>
      </header>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>{formatMessage({ id: 'fieldsets.settings-section' })}</h2>

        <div className={styles['settings-form']}>
          <div className={styles['settings-field']}>
            <label htmlFor="fieldset-description" className={styles['settings-label']}>
              {formatMessage({ id: 'fieldsets.settings.description' })}
            </label>
            <textarea
              id="fieldset-description"
              className={styles['settings-textarea']}
              value={detailFieldset.description}
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
              value={detailFieldset.labelPosition}
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
                labelPosition={isDesktop ? detailFieldset.labelPosition : EFieldLabelPosition.Top}
              />
            ))}
          </div>
        )}

        {sortedFields.length === 0 && (
          <p className={styles['empty-text']}>{formatMessage({ id: 'fieldsets.no-fields' })}</p>
        )}
      </div>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>{formatMessage({ id: 'fieldsets.rules-section' })}</h2>

        {detailFieldset.rules.length === 0 && (
          <p className={styles['empty-text']}>{formatMessage({ id: 'fieldsets.no-rules' })}</p>
        )}

        {detailFieldset.rules.map((rule, index) => (
          <div key={rule.apiName} className={styles['rule-row']}>
            <select
              value={rule.type}
              onChange={(e) => handleEditRuleType(index, e.target.value as EFieldsetRuleType)}
              className={styles['rule-value-input']}
              style={{ flex: 'none', minWidth: '10rem' }}
            >
              {FIELDSET_RULE_TYPES.map((ruleType) => (
                <option key={ruleType.value} value={ruleType.value}>
                  {formatMessage({ id: ruleType.labelKey })}
                </option>
              ))}
            </select>

            <input
              type="text"
              className={styles['rule-value-input']}
              value={rule.value ?? ''}
              placeholder={getRuleValuePlaceholder(rule.type)}
              onChange={(e) => handleEditRuleValue(index, e.target.value)}
            />

            <button type="button" className={styles['rule-delete-btn']} onClick={() => handleDeleteRule(index)}>
              {formatMessage({ id: 'fieldsets.rule-delete' })}
            </button>

            <div className={styles['rule-fields-selector']}>
              <span className={styles['rule-fields-label']}>{formatMessage({ id: 'fieldsets.rule-fields' })}</span>
              <div className={styles['rule-fields-select']}>
                <FilterSelect<'apiName', 'name', { apiName: string; name: string }>
                  isMultiple
                  optionIdKey="apiName"
                  optionLabelKey="name"
                  options={detailFieldset.fields.map((field) => ({ apiName: field.apiName, name: field.name }))}
                  selectedOptions={rule.fields || []}
                  placeholderText={formatMessage({ id: 'fieldsets.rule-fields-placeholder' })}
                  onChange={(fieldApiNames) => handleEditRuleFields(index, fieldApiNames)}
                  resetFilter={() => handleEditRuleFields(index, [])}
                  renderPlaceholder={(opts) => {
                    const selected = (rule.fields || []).length;
                    if (selected === 0) return formatMessage({ id: 'fieldsets.rule-fields-placeholder' });
                    const selectedNames = opts
                      .filter((option) => (rule.fields || []).includes(option.apiName))
                      .map((option) => option.name);
                    return selectedNames.join(', ');
                  }}
                />
              </div>
            </div>
          </div>
        ))}

        <button type="button" className={styles['add-rule-btn']} onClick={handleAddRule}>
          + {formatMessage({ id: 'fieldsets.add-rule' })}
        </button>
      </div>

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
