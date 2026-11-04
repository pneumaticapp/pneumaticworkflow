/* prettier-ignore */
import { connect } from 'react-redux';

import { IStepNameProps, StepNameComponent } from './StepName';
import type { RootState } from '../../redux/store';
import { loadTemplateVariables } from '../../redux/actions';

type TStoreProps = Pick<IStepNameProps, 'variables'>;
type TDispatchProps = Pick<IStepNameProps, 'loadTemplateVariables'>;
type TOwnProps = Pick<IStepNameProps, 'templateId'>;

const mapStateToProps = (
  { templates: { templatesVariablesMap } }: RootState,
  { templateId }: TOwnProps,
): TStoreProps => {
  const variables = templatesVariablesMap[templateId];

  return { variables };
};

const mapDispatchToProps: TDispatchProps = { loadTemplateVariables };

export const StepName = connect(mapStateToProps, mapDispatchToProps)(StepNameComponent);
