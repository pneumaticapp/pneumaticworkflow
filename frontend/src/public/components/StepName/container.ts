/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';

import { IStepNameProps, StepNameComponent } from './StepName';
import { IApplicationState } from '../../types/redux';
import { loadTemplateVariables } from '../../redux/actions';

type TStoreProps = Pick<IStepNameProps, 'variables'>;
type TDispatchProps = Pick<IStepNameProps, 'loadTemplateVariables'>;
type TOwnProps = Pick<IStepNameProps, 'templateId'>;

const mapStateToProps = (
  { templates: { templatesVariablesMap } }: IApplicationState,
  { templateId }: TOwnProps,
): TStoreProps => {
  const variables = templatesVariablesMap[templateId];

  return { variables };
};

const mapDispatchToProps: TDispatchProps = { loadTemplateVariables };

export const StepName = connect(mapStateToProps, mapDispatchToProps)(StepNameComponent);
