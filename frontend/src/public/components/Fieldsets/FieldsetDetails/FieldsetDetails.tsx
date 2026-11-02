import * as React from 'react';
import { useEffect, useState, useMemo, useCallback, useRef, ChangeEvent } from 'react';
import classnames from 'classnames';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';

import TextareaAutosize from 'react-textarea-autosize';

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
import { Select } from '../../UI/Select';
import { NotificationManager } from '../../UI/Notifications';
import { FieldsetModal } from '../FieldsetModal/FieldsetModal';
import { EFieldsetModalType } from '../FieldsetModal/types';
import { FieldsetDetailsSkeleton } from './FieldsetDetailsSkeleton';
import { FieldsetUnsavedChangesModal } from './FieldsetUnsavedChangesModal';

import { getCurrentFieldset, isCurrentFieldsetLoading } from '../../../redux/selectors/fieldsets';
import { getAccountId } from '../../../redux/selectors/user';

import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../types/template';
import { FilledInfoIcon, ArrowDropdownIcon, DateIcon, LinkIcon } from '../../icons';
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
import { SINGLE_LINE_FIELD_TYPES } from './constants';
import { validateFieldsetRules } from '../validators';
import {
  FIELDSET_LABEL_POSITION_OPTIONS,
  FIELDSET_RULE_TYPES,
  FIELDSET_RULE_VALUE_PLACEHOLDER_BY_TYPE,
} from '../constants';

import { useCheckDevice } from '../../../hooks/useCheckDevice';

import { TFieldsetDetailsProps, TDetailFieldsetState, TDetailFieldsetChanges } from './types';
import styles from './FieldsetDetails.css';

const READONLY_FIELD_ICONS: Partial<Record<EExtraFieldType, React.FC<React.SVGAttributes<SVGElement>>>> = {
  [EExtraFieldType.User]: ArrowDropdownIcon,
  [EExtraFieldType.Date]: DateIcon,
  [EExtraFieldType.Url]: LinkIcon,
};

const EMPTY_DETAIL_FIELDSET: TDetailFieldsetState = {
  title: '',
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
  const labelPositionRef = useRef<HTMLDivElement>(null);

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
      title: fieldset.title,
      description: fieldset.description || '',
      labelPosition: fieldset.labelPosition,
      fields: normalizeFieldsForUI(fieldset.fields as unknown as IExtraField[]),
      rules: fieldset.rules || [],
    });
    setDetailFieldsetChanges({});
  }, [
    fieldset?.id,
    fieldset?.title,
    fieldset?.description,
    fieldset?.labelPosition,
    fieldset?.fields,
    fieldset?.rules,
  ]);

  const labelPositionOptions = useMemo(
    () =>
      FIELDSET_LABEL_POSITION_OPTIONS.map((option) => ({
        value: option.value,
        label: formatMessage({ id: option.labelKey }),
      })),
    [formatMessage],
  );

  const ruleTypeOptions = useMemo(
    () =>
      FIELDSET_RULE_TYPES.map((option) => ({
        value: option.value,
        label: formatMessage({ id: option.labelKey }),
      })),
    [formatMessage],
  );

  const fieldOptions = detailFieldset.fields.map((field) => ({ value: field.apiName, label: field.name }));
  const getSelectedFieldOptions = (fieldApiNames: string[] = []) =>
    fieldOptions.filter((option) => fieldApiNames.includes(option.value));

  const handleSettingsTitleChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const title = event.target.value;
    setDetailFieldset((prev) => ({ ...prev, title }));
    setDetailFieldsetChanges((prev) => ({ ...prev, title }));
  };

  const handleSettingsDescriptionChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const description = event.target.value;
    setDetailFieldset((prev) => ({ ...prev, description }));
    setDetailFieldsetChanges((prev) => ({ ...prev, description }));
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

  const handleRuleTypeChange =
    (index: number, currentType: EFieldsetRuleType) =>
    ({ value }: { value: EFieldsetRuleType }) => {
      if (value !== currentType) handleEditRuleType(index, value);
    };

  const handleLabelPositionChange = ({ value }: { value: EFieldLabelPosition }) => {
    if (value === detailFieldset.labelPosition) return;
    setDetailFieldset((prev) => ({ ...prev, labelPosition: value }));
    setDetailFieldsetChanges((prev) => ({ ...prev, labelPosition: value }));
  };

  const handleEditRuleFields = (index: number, fieldApiNames: string[]) => {
    const rules = detailFieldset.rules.map((rule, i) => (i === index ? { ...rule, fields: fieldApiNames } : rule));
    setDetailFieldset((prev) => ({ ...prev, rules }));
    setDetailFieldsetChanges((prev) => ({ ...prev, rules }));
  };

  const handleDeleteRule = (index: number) => {
    const rules = detailFieldset.rules.filter((_, i) => i !== index);
    setDetailFieldset((prev) => ({ ...prev, rules }));
    setDetailFieldsetChanges((prev) => ({ ...prev, rules }));
  };

  const handleSave = (onSuccess?: () => void): void => {
    if (!fieldset || !isChanged) return;

    const titleErrorMessageKey = validateFieldsetTitle(detailFieldset.title);

    if (titleErrorMessageKey) {
      NotificationManager.warning({
        message: formatMessage({ id: titleErrorMessageKey }),
      });
      return;
    }

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
      onSuccess,
    };

    if (detailFieldsetChanges.title !== undefined) {
      payload.title = detailFieldsetChanges.title;
    }
    if (detailFieldsetChanges.description !== undefined) {
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

  const isLinked = fieldset.usage.length > 0;
  const readOnlyBadge = isLinked ? (
    <span className={styles['readonly-badge']}>{formatMessage({ id: 'fieldsets.readonly-badge' })}</span>
  ) : null;

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
      <FieldsetUnsavedChangesModal isChanged={isChanged} onSave={handleSave} />

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
            onClone={handleCloneFieldset}
            editLabel={formatMessage({ id: 'fieldsets.edit' })}
            deleteLabel={formatMessage({ id: 'fieldsets.delete' })}
            cloneLabel={formatMessage({ id: 'fieldsets.clone' })}
            isReadOnly={isLinked}
            toggleType={EModifyDropdownToggle.Modify}
          />
        </div>
      </header>

      {isLinked ? (
        <div className={`${styles['usage-banner']} ${styles['usage-banner--linked']}`}>
          <div className={styles['usage-banner__row']}>
            <span>{formatMessage({ id: 'fieldsets.usage.linked' }, { count: fieldset.usage.length })}</span>
            <Select
              controlSize="sm"
              className={styles['usage-banner__dropdown']}
              title={formatMessage({ id: 'fieldsets.usage.show' })}
              options={fieldset.usage.map((template) => ({
                value: template.name,
                label: (
                  <Tooltip
                    content={template.name}
                    placement="top"
                    interactive={false}
                    appendTo={() => document.body}
                    containerClassName={styles['usage-banner__option-tooltip']}
                    contentClassName={styles['usage-banner__tooltip-content']}
                  >
                    <span>{template.name}</span>
                  </Tooltip>
                ),
              }))}
              filterOption={(option, inputValue) =>
                (option.data as { value: string }).value?.toLowerCase().includes(inputValue.toLowerCase()) ?? true
              }
              placement="left"
              classNames={{
                menuList: () => styles['usage-banner__menu-list'],
                option: () => styles['usage-banner__option'],
              }}
            />
          </div>
        </div>
      ) : (
        <div className={`${styles['usage-banner']} ${styles['usage-banner--not-linked']}`}>
          {formatMessage({ id: 'fieldsets.usage.not-linked' })}
        </div>
      )}

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>
          {formatMessage({ id: 'fieldsets.settings-section' })}
          {readOnlyBadge}
        </h2>

        <div className={styles['settings-form']}>
          <div className={styles['settings-field']}>
            <label htmlFor="fieldset-title" className={styles['settings-label']}>
              {formatMessage({ id: 'fieldsets.settings.title' })}
              <Tooltip content={formatMessage({ id: 'fieldsets.settings.title-tooltip' })} placement="top">
                <span>
                  <FilledInfoIcon />
                </span>
              </Tooltip>
            </label>
            {isLinked ? (
              <TextareaAutosize
                id="fieldset-title"
                minRows={1}
                className={styles['settings-title']}
                value={detailFieldset.title}
                disabled
              />
            ) : (
              <input
                id="fieldset-title"
                type="text"
                className={classnames(
                  styles['settings-title'],
                  Boolean(validateFieldsetTitle(detailFieldset.title)) && styles['settings-title_error'],
                )}
                value={detailFieldset.title}
                placeholder={formatMessage({ id: 'fieldsets.settings.title-placeholder' })}
                onChange={handleSettingsTitleChange}
              />
            )}
          </div>

          <div className={styles['settings-field']}>
            <label htmlFor="fieldset-description" className={styles['settings-label']}>
              {formatMessage({ id: 'fieldsets.settings.description' })}
              <Tooltip content={formatMessage({ id: 'fieldsets.settings.description-tooltip' })} placement="top">
                <span className={styles['settings-info-icon']}>
                  <FilledInfoIcon />
                </span>
              </Tooltip>
            </label>
            {isLinked ? (
              <TextareaAutosize
                id="fieldset-description"
                minRows={3}
                className={styles['settings-description']}
                value={detailFieldset.description}
                disabled
              />
            ) : (
              <textarea
                id="fieldset-description"
                className={styles['settings-description']}
                value={detailFieldset.description}
                placeholder={formatMessage({ id: 'fieldsets.settings.description-placeholder' })}
                onChange={handleSettingsDescriptionChange}
              />
            )}
          </div>

          <div className={styles['settings-field']}>
            <span
              role="button"
              tabIndex={0}
              className={styles['settings-label']}
              onClick={() => labelPositionRef.current?.querySelector<HTMLButtonElement>('button')?.focus()}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  labelPositionRef.current?.querySelector<HTMLButtonElement>('button')?.focus();
                }
              }}
            >
              {formatMessage({ id: 'fieldsets.settings.label-position' })}
            </span>
            <div ref={labelPositionRef}>
              <Select
                className={styles['settings-select']}
                isDisabled={isLinked}
                options={labelPositionOptions}
                value={labelPositionOptions.find((option) => option.value === detailFieldset.labelPosition) ?? null}
                onChange={handleLabelPositionChange}
              />
            </div>
          </div>
        </div>
      </div>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>
          {formatMessage({ id: 'fieldsets.fields-section' })}
          {readOnlyBadge}
        </h2>

        <div className={classnames(styles['components'], isLinked && styles['components_disabled'])}>
          {ExtraFieldsMap.map((x) => (
            <ExtraFieldIcon {...x} key={x.id} onClick={() => handleCreateField(x.id)} disabled={isLinked} />
          ))}
        </div>

        {sortedFields.length > 0 && (
          <div className={classnames(styles['fields'], isLinked && styles['fieldset_readonly'])}>
            {sortedFields.map((field, index) => {
              const readOnlyField =
                isLinked && SINGLE_LINE_FIELD_TYPES.has(field.type) ? { ...field, type: EExtraFieldType.Text } : field;

              const IconComponent = isLinked && READONLY_FIELD_ICONS[field.type];

              return (
                <ExtraFieldIntl
                  key={field.apiName}
                  id={index}
                  field={readOnlyField}
                  fieldsCount={sortedFields.length}
                  labelBackgroundColor={EInputNameBackgroundColor.White}
                  deleteField={() => handleDeleteField(index)}
                  moveFieldUp={() => handleMoveField(index, EMoveDirections.Up)}
                  moveFieldDown={() => handleMoveField(index, EMoveDirections.Down)}
                  editField={handleEditField(field.apiName)}
                  accountId={accountId}
                  mode={EExtraFieldMode.Kickoff}
                  showDropdown
                  isDisabled={isLinked}
                  isFieldsetReadOnly={isLinked}
                  datasetOptions={datasetOptions}
                  labelPosition={isDesktop ? detailFieldset.labelPosition : EFieldLabelPosition.Top}
                  {...(IconComponent && { icon: <IconComponent /> })}
                />
              );
            })}
          </div>
        )}

        {sortedFields.length === 0 && (
          <p className={styles['empty-text']}>{formatMessage({ id: 'fieldsets.no-fields' })}</p>
        )}
      </div>

      <div className={styles['list']}>
        <h2 className={styles['section-title']}>
          {formatMessage({ id: 'fieldsets.rules-section' })}
          {readOnlyBadge}
        </h2>

        {detailFieldset.rules.length === 0 && (
          <p className={styles['empty-text']}>{formatMessage({ id: 'fieldsets.no-rules' })}</p>
        )}

        {detailFieldset.rules.map((rule, index) => (
          <div key={rule.apiName} className={styles['rule-row']}>
            <Select
              className={styles['settings-select']}
              isDisabled={isLinked}
              options={ruleTypeOptions}
              value={ruleTypeOptions.find((option) => option.value === rule.type) ?? null}
              onChange={handleRuleTypeChange(index, rule.type)}
            />

            <input
              type="text"
              className={styles['rule-value-input']}
              value={rule.value ?? ''}
              placeholder={getRuleValuePlaceholder(rule.type)}
              onChange={(e) => handleEditRuleValue(index, e.target.value)}
              disabled={isLinked}
            />

            {!isLinked && (
              <button type="button" className={styles['rule-delete-btn']} onClick={() => handleDeleteRule(index)}>
                {formatMessage({ id: 'fieldsets.rule-delete' })}
              </button>
            )}

            <div className={styles['rule-fields-selector']}>
              <span className={styles['rule-fields-label']}>{formatMessage({ id: 'fieldsets.rule-fields' })}</span>
              <div className={styles['rule-fields-select']}>
                <Select
                  controlSize="sm"
                  isSearchable={false}
                  controlVariant="accent"
                  isMulti
                  isDisabled={isLinked}
                  title={
                    getSelectedFieldOptions(rule.fields)
                      .map((option) => option.label)
                      .join(', ') || formatMessage({ id: 'fieldsets.rule-fields-placeholder' })
                  }
                  noOptionsMessage={() => formatMessage({ id: 'fieldsets.no-fields' })}
                  options={fieldOptions}
                  value={getSelectedFieldOptions(rule.fields)}
                  onChange={(selected: { value: string }[]) =>
                    handleEditRuleFields(
                      index,
                      selected.map((option) => option.value),
                    )
                  }
                  onClear={rule.fields?.length ? () => handleEditRuleFields(index, []) : undefined}
                />
              </div>
            </div>
          </div>
        ))}

        {!isLinked && (
          <button type="button" className={styles['add-rule-btn']} onClick={handleAddRule}>
            + {formatMessage({ id: 'fieldsets.add-rule' })}
          </button>
        )}
      </div>

      {!isLinked && (
        <div className={styles['save-bar']}>
          <Button
            label={formatMessage({ id: 'fieldsets.save' })}
            buttonStyle="yellow"
            size="md"
            onClick={() => handleSave()}
            disabled={!isChanged}
          />
          {isChanged && (
            <span className={styles['save-bar__hint']}>{formatMessage({ id: 'fieldsets.unsaved-changes' })}</span>
          )}
        </div>
      )}

      <FieldsetModal type={EFieldsetModalType.Edit} />
    </div>
  );
};

export default FieldsetDetails;
