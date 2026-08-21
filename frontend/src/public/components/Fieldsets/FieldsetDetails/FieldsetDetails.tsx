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

import { ModifyDropdown, Button, Tooltip, FilterSelect } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';
import { DropdownList } from '../../UI/DropdownList';
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
import { SINGLE_LINE_FIELD_TYPES } from './constants';
import { validateFieldsetRules } from '../validators';
import { FIELDSET_LABEL_POSITION_OPTIONS } from '../constants';

import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { TFieldsetDetailsProps, TLocalFieldsetState, TFieldsetChanges } from './types';
import { FieldsetRulesets } from './FieldsetRulesets/FieldsetRulesets';
import styles from './FieldsetDetails.css';

const READONLY_FIELD_ICONS: Partial<Record<EExtraFieldType, React.FC<React.SVGAttributes<SVGElement>>>> = {
  [EExtraFieldType.User]: ArrowDropdownIcon,
  [EExtraFieldType.Date]: DateIcon,
  [EExtraFieldType.Url]: LinkIcon,
};

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
  const labelPositionRef = useRef<HTMLDivElement>(null);

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

  const labelPositionOptions = useMemo(
    () =>
      FIELDSET_LABEL_POSITION_OPTIONS.map((option) => ({
        id: option.value,
        name: formatMessage({ id: option.labelKey }),
      })),
    [formatMessage],
  );

  const handleSettingsTitleChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const title = event.target.value;
    setLocalFieldset((prev) => ({ ...prev, title }));
    setFieldsetChanges((prev) => ({ ...prev, title }));
  };

  const handleSettingsDescriptionChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const description = event.target.value;
    setLocalFieldset((prev) => ({ ...prev, description }));
    setFieldsetChanges((prev) => ({ ...prev, description }));
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

  const handleSave = (onSuccess?: () => void): void => {
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
      onSuccess,
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


  const isTitleError =
    (fieldsetChanges.title !== undefined || Boolean(localFieldset.title)) &&
    Boolean(validateFieldsetTitle(localFieldset.title));

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
                })
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
            <span>
              {formatMessage({ id: 'fieldsets.usage.linked' }, { count: fieldset.usage.length })}
            </span>
            <DropdownList
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
              <Tooltip
                content={formatMessage({ id: 'fieldsets.settings.title-tooltip' })}
                placement="top"
              >
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
                value={localFieldset.title}
                disabled
              />
            ) : (
              <input
                id="fieldset-title"
                type="text"
                className={classnames(
                  styles['settings-title'],
                  isTitleError && styles['settings-title_error'],
                )}
                value={localFieldset.title}
                placeholder={formatMessage({ id: 'fieldsets.settings.title-placeholder' })}
                onChange={handleSettingsTitleChange}
              />
            )}
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
            {isLinked ? (
              <TextareaAutosize
                id="fieldset-description"
                minRows={3}
                className={styles['settings-description']}
                value={localFieldset.description}
                disabled
              />
            ) : (
              <textarea
                id="fieldset-description"
                className={styles['settings-description']}
                value={localFieldset.description}
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
            <FilterSelect<'id', 'name', { id: EFieldLabelPosition; name: string }>
              optionIdKey="id"
              optionLabelKey="name"
              options={labelPositionOptions}
              selectedOption={localFieldset.labelPosition}
              onChange={(key) => {
                if (key && key !== localFieldset.labelPosition) {
                  setLocalFieldset((prev) => ({ ...prev, labelPosition: key as EFieldLabelPosition }));
                  setFieldsetChanges((prev) => ({ ...prev, labelPosition: key as EFieldLabelPosition }));
                }
              }}
              resetFilter={() => {}}
              placeholderText=""
              isDisabled={isLinked}
              containerClassname={styles['settings-select']}
              toggleClassName={styles['settings-select__toggle']}
              menuClassName={styles['settings-select__menu']}
              renderPlaceholder={() => labelPositionOptions.find((option) => option.id === localFieldset.labelPosition)?.name || ''}
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
            <ExtraFieldIcon
              {...x}
              key={x.id}
              onClick={() => handleCreateField(x.id)}
              disabled={isLinked}
            />
          ))}
        </div>

        {sortedFields.length > 0 && (
          <div className={classnames(styles['fields'], isLinked && styles['fieldset_readonly'])}>
            {sortedFields.map((field, index) => {
              const readOnlyField =
                isLinked && SINGLE_LINE_FIELD_TYPES.has(field.type)
                  ? { ...field, type: EExtraFieldType.Text }
                  : field;

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
                  labelPosition={isDesktop ? localFieldset.labelPosition : EFieldLabelPosition.Top}
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

      <FieldsetRulesets
        rulesets={localFieldset.rulesets}
        fields={localFieldset.fields}
        onRulesetsChange={handleRulesetsChange}
        isReadOnly={isLinked}
      />

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
