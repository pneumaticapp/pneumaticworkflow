import * as React from 'react';
import { useEffect, useState, useMemo, useCallback } from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import {
  openEditModal,
  deleteFieldsetAction,
  loadCurrentFieldset,
  resetCurrentFieldset,
  updateFieldsetAction,
  setTemplateId,
} from '../../../redux/fieldsets/slice';


import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { ModifyDropdown, Button, FilterSelect } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { EFieldsetModalType } from '../FieldsetModal/types';
import { FieldsetDetailsSkeleton } from './FieldsetDetailsSkeleton';

import { getCurrentFieldset, isCurrentFieldsetLoading } from '../../../redux/selectors/fieldsets';
import { getAccountId } from '../../../redux/selectors/user';


import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../types/template';
import { EInputNameBackgroundColor, EMoveDirections } from '../../../types/workflow';
import { IFieldsetTemplateRule, TFieldLabelPosition } from '../../../types/fieldset';
import { ExtraFieldsMap } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../../TemplateEdit/ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../../TemplateEdit/ExtraFields';
import { getEmptyField } from '../../TemplateEdit/KickoffRedux/utils/getEmptyField';
import { getEditedFields } from '../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../utils/workflows';

import { normalizeFieldsForUI } from './fieldsetFieldMappers';


import { TFieldsetDetailsProps } from './types';
import styles from './FieldsetDetails.css';

const RULE_TYPES = [
  { value: 'sum_equal', labelKey: 'fieldsets.rule-type-sum_equal' },
] as const;

const LABEL_POSITION_OPTIONS: { value: TFieldLabelPosition; labelKey: string }[] = [
  { value: 'top', labelKey: 'fieldsets.settings.label-position.top' },
  { value: 'left', labelKey: 'fieldsets.settings.label-position.left' },
];



const FieldsetDetails = ({ match: { params: { id: matchParamId, templateId: matchTemplateId } } }: TFieldsetDetailsProps) => {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const fieldset = useSelector(getCurrentFieldset);
  const isLoading = useSelector(isCurrentFieldsetLoading);
  const accountId = useSelector(getAccountId);


  const [localFields, setLocalFields] = useState<IExtraField[]>([]);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const [localRules, setLocalRules] = useState<IFieldsetTemplateRule[]>([]);
  const [hasUnsavedRuleChanges, setHasUnsavedRuleChanges] = useState(false);

  // Settings local state
  const [localDescription, setLocalDescription] = useState('');
  const [localLabelPosition, setLocalLabelPosition] = useState<TFieldLabelPosition>('top');

  const [hasUnsavedSettingsChanges, setHasUnsavedSettingsChanges] = useState(false);

  const fieldsetListRoute = ERoutes.TemplateFieldsets.replace(':templateId', matchTemplateId);




  useEffect(() => {
    const id = Number(matchParamId);
    if (Number.isNaN(id)) {
      history.push(fieldsetListRoute);

      return;
    }
    if (fieldset?.id === id) return;

    dispatch(setTemplateId(Number(matchTemplateId)));
    dispatch(loadCurrentFieldset({ id }));
  }, [matchParamId]);



  useEffect(() => {
    return () => {
      dispatch(resetCurrentFieldset());
    };
  }, []);

  // Sync local fields when fieldset loads/updates from server
  useEffect(() => {
    if (fieldset?.fields) {
      setLocalFields(normalizeFieldsForUI(fieldset.fields as unknown as IExtraField[]));
      setHasUnsavedChanges(false);
    }
  }, [fieldset?.fields]);

  // Sync local rules when fieldset loads/updates from server
  useEffect(() => {
    if (fieldset?.rules) {
      setLocalRules(fieldset.rules);
      setHasUnsavedRuleChanges(false);
    }
  }, [fieldset?.rules]);

  // Sync settings when fieldset loads/updates from server
  useEffect(() => {
    if (fieldset) {
      setLocalDescription(fieldset.description || '');
      setLocalLabelPosition(fieldset.labelPosition || 'top');
      setHasUnsavedSettingsChanges(false);
    }
  }, [
    fieldset?.id,
    fieldset?.description,
    fieldset?.labelPosition,
  ]);

  const handleSettingsDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setLocalDescription(e.target.value);
    setHasUnsavedSettingsChanges(true);
  };

  const handleSettingsLabelPositionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLocalLabelPosition(e.target.value as TFieldLabelPosition);
    setHasUnsavedSettingsChanges(true);
  };



  const handleSaveSettings = () => {
    if (!fieldset) return;
    dispatch(updateFieldsetAction({
      id: fieldset.id,
      description: localDescription,
      label_position: localLabelPosition,
    }));
    setHasUnsavedSettingsChanges(false);
  };

  const getSortedFields = useCallback(() => {
    return [...localFields].sort((a, b) => b.order - a.order);
  }, [localFields]);

  const sortedFields = useMemo(() => getSortedFields(), [getSortedFields]);

  const handleCreateField = (type: EExtraFieldType) => {
    const newFields = getNormalizeFieldsOrders([...localFields, getEmptyField(type, formatMessage)]);
    setLocalFields(newFields);
    setHasUnsavedChanges(true);
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const newFields = getEditedFields(getSortedFields(), apiName, changedProps);
    setLocalFields(newFields);
    setHasUnsavedChanges(true);
  };

  const handleDeleteField = (idx: number) => {
    const newFields = getSortedFields().filter((_, index) => index !== idx);
    setLocalFields(getNormalizeFieldsOrders(newFields));
    setHasUnsavedChanges(true);
  };

  const handleMoveField = (from: number, direction: EMoveDirections) => {
    const to = direction === EMoveDirections.Up ? from - 1 : from + 1;
    const newFields = moveWorkflowField(from, to, getSortedFields());
    setLocalFields(newFields);
    setHasUnsavedChanges(true);
  };

  const handleSaveFields = () => {
    if (!fieldset) return;
    const fieldsPayload = localFields.map(({ id: _id, ...rest }) => rest);
    dispatch(updateFieldsetAction({
      id: fieldset.id,
      fields: fieldsPayload as any,
    }));
    setHasUnsavedChanges(false);
  };

  // Rules handlers
  const handleAddRule = () => {
    const newRule: IFieldsetTemplateRule = {
      id: -(Date.now()),  // temporary negative id for new rules
      type: RULE_TYPES[0].value,
      value: '',
      fields: [],
    };
    setLocalRules([...localRules, newRule]);
    setHasUnsavedRuleChanges(true);
  };

  const handleEditRuleValue = (index: number, value: string) => {
    const updated = localRules.map((rule, i) =>
      i === index ? { ...rule, value } : rule,
    );
    setLocalRules(updated);
    setHasUnsavedRuleChanges(true);
  };

  const handleEditRuleType = (index: number, type: string) => {
    const updated = localRules.map((rule, i) =>
      i === index ? { ...rule, type } : rule,
    );
    setLocalRules(updated);
    setHasUnsavedRuleChanges(true);
  };

  const handleEditRuleFields = (index: number, fieldApiNames: (string | number | null)[]) => {
    const updated = localRules.map((rule, i) =>
      i === index ? { ...rule, fields: fieldApiNames.filter((n): n is string => typeof n === 'string') } : rule,
    );
    setLocalRules(updated);
    setHasUnsavedRuleChanges(true);
  };

  const handleDeleteRule = (index: number) => {
    setLocalRules(localRules.filter((_, i) => i !== index));
    setHasUnsavedRuleChanges(true);
  };

  const handleSaveRules = () => {
    if (!fieldset) return;
    // Strip temporary negative ids for new rules so the backend creates them
    const rulesPayload = localRules.map((rule) => ({
      ...rule,
      id: rule.id > 0 ? rule.id : undefined,
    }));
    dispatch(updateFieldsetAction({
      id: fieldset.id,
      rules: rulesPayload as IFieldsetTemplateRule[],
    }));
    setHasUnsavedRuleChanges(false);
  };

  if (isLoading || !fieldset) {
    return <FieldsetDetailsSkeleton />;
  }

  return (
    <div className={styles['container']}>
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
        <h2 className={styles['section-title']}>
          {formatMessage({ id: 'fieldsets.settings-section' })}
        </h2>

        <div className={styles['settings-form']}>
          <div className={styles['settings-field']}>
            <label htmlFor="fieldset-description" className={styles['settings-label']}>
              {formatMessage({ id: 'fieldsets.settings.description' })}
            </label>
            <textarea
              id="fieldset-description"
              className={styles['settings-textarea']}
              value={localDescription}
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
              value={localLabelPosition}
              onChange={handleSettingsLabelPositionChange}
            >
              {LABEL_POSITION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {formatMessage({ id: opt.labelKey })}
                </option>
              ))}
            </select>
          </div>


        </div>

        {hasUnsavedSettingsChanges && (
          <div className={styles['save-bar']}>
            <Button
              label={formatMessage({ id: 'fieldsets.save-settings' })}
              buttonStyle="yellow"
              size="md"
              onClick={handleSaveSettings}
            />
            <span className={styles['save-bar__hint']}>
              {formatMessage({ id: 'fieldsets.unsaved-settings-changes' })}
            </span>
          </div>
        )}
      </div>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>
          {formatMessage({ id: 'fieldsets.fields-section' })}
        </h2>

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
              />
            ))}
          </div>
        )}

        {sortedFields.length === 0 && (
          <p className={styles['empty-text']}>
            {formatMessage({ id: 'fieldsets.no-fields' })}
          </p>
        )}

        {hasUnsavedChanges && (
          <div className={styles['save-bar']}>
            <Button
              label={formatMessage({ id: 'fieldsets.save-fields' })}
              buttonStyle="yellow"
              size="md"
              onClick={handleSaveFields}
            />
            <span className={styles['save-bar__hint']}>
              {formatMessage({ id: 'fieldsets.unsaved-changes' })}
            </span>
          </div>
        )}
      </div>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>
          {formatMessage({ id: 'fieldsets.rules-section' })}
        </h2>

        {localRules.length === 0 && !hasUnsavedRuleChanges && (
          <p className={styles['empty-text']}>
            {formatMessage({ id: 'fieldsets.no-rules' })}
          </p>
        )}

        {localRules.map((rule, index) => (
          <div key={rule.id} className={styles['rule-row']}>
            <select
              value={rule.type}
              onChange={(e) => handleEditRuleType(index, e.target.value)}
              className={styles['rule-value-input']}
              style={{ flex: 'none', minWidth: '10rem' }}
            >
              {RULE_TYPES.map((rt) => (
                <option key={rt.value} value={rt.value}>
                  {formatMessage({ id: rt.labelKey })}
                </option>
              ))}
            </select>

            <input
              type="text"
              className={styles['rule-value-input']}
              value={rule.value}
              placeholder={formatMessage({ id: 'fieldsets.rule-value-placeholder' })}
              onChange={(e) => handleEditRuleValue(index, e.target.value)}
            />

            <button
              type="button"
              className={styles['rule-delete-btn']}
              onClick={() => handleDeleteRule(index)}
            >
              {formatMessage({ id: 'fieldsets.rule-delete' })}
            </button>

            <div className={styles['rule-fields-selector']}>
              <span className={styles['rule-fields-label']}>
                {formatMessage({ id: 'fieldsets.rule-fields' })}
              </span>
              <div className={styles['rule-fields-select']}>
                <FilterSelect<'apiName', 'name', { apiName: string; name: string }>
                  isMultiple
                  optionIdKey="apiName"
                  optionLabelKey="name"
                  options={localFields.map((f) => ({ apiName: f.apiName, name: f.name }))}
                  selectedOptions={rule.fields || []}
                  placeholderText={formatMessage({ id: 'fieldsets.rule-fields-placeholder' })}
                  selectAllLabel={formatMessage({ id: 'fieldsets.rule-fields-all' })}
                  onChange={(fieldApiNames) => handleEditRuleFields(index, fieldApiNames)}
                  resetFilter={() => handleEditRuleFields(index, [])}
                  renderPlaceholder={(opts) => {
                    const selected = (rule.fields || []).length;
                    if (selected === 0) return formatMessage({ id: 'fieldsets.rule-fields-placeholder' });
                    const selectedNames = opts
                      .filter((o) => (rule.fields || []).includes(o.apiName))
                      .map((o) => o.name);
                    return selectedNames.join(', ');
                  }}
                />
              </div>
            </div>
          </div>
        ))}

        <button
          type="button"
          className={styles['add-rule-btn']}
          onClick={handleAddRule}
        >
          + {formatMessage({ id: 'fieldsets.add-rule' })}
        </button>

        {hasUnsavedRuleChanges && (
          <div className={styles['save-bar']}>
            <Button
              label={formatMessage({ id: 'fieldsets.save-rules' })}
              buttonStyle="yellow"
              size="md"
              onClick={handleSaveRules}
            />
            <span className={styles['save-bar__hint']}>
              {formatMessage({ id: 'fieldsets.unsaved-rule-changes' })}
            </span>
          </div>
        )}
      </div>

      <FieldsetModal type={EFieldsetModalType.Edit} />
    </div>
  );
};

export default FieldsetDetails;

