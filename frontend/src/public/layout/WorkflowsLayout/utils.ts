import { EWorkflowsView } from '../../types/workflow';
import { getQueryStringByParams, getQueryStringParams, history } from '../../utils/history';

export const updateQueryFields = (
  selectedFieldsByTemplate: Record<string, string[]>,
  templatesIdsFilter: number[],
  workflowsView: EWorkflowsView,
) => {
  const currentParams = getQueryStringParams(window.location.search);

  if (workflowsView !== EWorkflowsView.Table || !templatesIdsFilter.length) {
    delete currentParams.fields;
  } else {
    const currentFields = selectedFieldsByTemplate[templatesIdsFilter[0]];
    if (currentFields?.length > 0) {
      currentParams.fields = currentFields.join(',');
    } else {
      delete currentParams.fields;
    }
  }

  const newQueryString = getQueryStringByParams(currentParams);
  history.push({ search: newQueryString });
};
