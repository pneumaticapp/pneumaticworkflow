import * as React from 'react';
import { injectIntl, IntlShape } from 'react-intl';
import classNames from 'classnames';

import { EMoveDirections, EInputNameBackgroundColor } from '../../../types/workflow';
import { EExtraFieldMode, EExtraFieldType, IExtraField } from '../../../types/template';
import { isArrayWithItems } from '../../../utils/helpers';
import { getNormalizeFieldsOrders, moveWorkflowField } from '../../../utils/workflows';

import { ExtraFieldsMap } from '../ExtraFields/utils/ExtraFieldsMap';
import { ExtraFieldIcon } from '../ExtraFields/utils/ExtraFieldIcon';
import { ExtraFieldIntl } from '../ExtraFields';
import { getEditedFields } from '../ExtraFields/utils/getEditedFields';
import { getEmptyField } from '../KickoffRedux/utils/getEmptyField';

import { OutputFormTaskMerged, IOutputFormTaskMergedOwnProps } from './OutputFormTaskMerged';

import styles from './OutputForm.css';
import stylesTaskForm from '../TaskForm/TaskForm.css';
import { useDatasetOptions } from '../ExtraFields/utils/useDatasetOptions';

export interface IOutputFormSimpleOwnProps {
  mode?: 'simple';
  fields: IExtraField[];
  onOutputChange(value: IExtraField[]): void;
  show?: boolean;
  isDisabled: boolean;
  accountId: number;
}

export type IOutputFormTaskMergedExternalProps = Omit<IOutputFormTaskMergedOwnProps, 'intl'> & {
  mode: 'taskMerged';
};

export type IOutputFormExternalProps = IOutputFormSimpleOwnProps | IOutputFormTaskMergedExternalProps;

export type ITaskOutputFlowFormProps = Omit<IOutputFormTaskMergedExternalProps, 'mode'>;

type TOutputFormInjectedProps = IOutputFormExternalProps & { intl: IntlShape };

function OutputFormSimple({
  fields,
  onOutputChange,
  intl,
  isDisabled,
  show,
  accountId,
}: IOutputFormSimpleOwnProps & { intl: IntlShape }) {
  const outputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (show) {
      outputRef.current?.focus();
    }
  }, [show]);

  const sortedFields = [...fields].sort((a, b) => b.order - a.order);
  const datasetOptions = useDatasetOptions(fields);

  const isFormEmpty = !isArrayWithItems(fields);

  const handleCreateField = (type: EExtraFieldType) => {
    const newFields = [...sortedFields, getEmptyField(type, intl.formatMessage)];

    onOutputChange(getNormalizeFieldsOrders(newFields));
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    const newFields = getEditedFields(sortedFields, apiName, changedProps);
    onOutputChange(newFields);
  };

  const handleDeleteField = (idx: number) => {
    if (!onOutputChange) {
      return;
    }

    const newOutputFields = sortedFields.filter((_, index) => index !== idx);

    onOutputChange(getNormalizeFieldsOrders(newOutputFields));
  };

  const handleMoveField = (idx: number, direction: EMoveDirections) => {
    if (!onOutputChange) {
      return;
    }

    const to = direction === EMoveDirections.Up ? idx - 1 : idx + 1;

    const newOutputFields = moveWorkflowField(idx, to, sortedFields);

    onOutputChange(newOutputFields);
  };

  const renderOutputIcons = () => (
    <div className={classNames(styles['components'], stylesTaskForm['content-mt16'])}>
      {ExtraFieldsMap.map((field) => (
        <ExtraFieldIcon {...field} key={field.id} onClick={() => handleCreateField(field.id)} />
      ))}
    </div>
  );

  return (
    <>
      {!isDisabled && renderOutputIcons()}

      {!isFormEmpty && (
        <div className={styles['fields']}>
          {sortedFields.map((field, index) => (
            <ExtraFieldIntl
              key={field.apiName}
              id={index}
              field={{ ...field }}
              fieldsCount={sortedFields.length}
              labelBackgroundColor={EInputNameBackgroundColor.White}
              deleteField={() => handleDeleteField(index)}
              moveFieldUp={() => handleMoveField(index, EMoveDirections.Up)}
              moveFieldDown={() => handleMoveField(index, EMoveDirections.Down)}
              editField={handleEditField(field.apiName)}
              mode={EExtraFieldMode.Kickoff}
              datasetOptions={datasetOptions}
              isDisabled={isDisabled}
              innerRef={outputRef}
              accountId={accountId}
            />
          ))}
        </div>
      )}
    </>
  );
}

function OutputForm(props: TOutputFormInjectedProps) {
  const { intl, ...rest } = props;
  if (rest.mode === 'taskMerged') {
    const { mode, ...merged } = rest as IOutputFormTaskMergedExternalProps;
    if (mode !== 'taskMerged') {
      return null;
    }
    return <OutputFormTaskMerged {...merged} intl={intl} />;
  }
  return <OutputFormSimple {...rest} intl={intl} />;
}

export const OutputFormIntl = injectIntl(OutputForm);
