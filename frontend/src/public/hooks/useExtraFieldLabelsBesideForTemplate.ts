import { useSelector } from 'react-redux';

import { IApplicationState } from '../types/redux';
import { selectExtraFieldLabelsBesideForTemplate } from '../redux/selectors/templateViewPreferences';

export const useExtraFieldLabelsBesideForTemplate = (templateId: number | undefined): boolean =>
  useSelector((state: IApplicationState) => selectExtraFieldLabelsBesideForTemplate(state, templateId));
