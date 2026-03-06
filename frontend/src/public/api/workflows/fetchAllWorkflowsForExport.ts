import { getWorkflows, IGetWorkflowsConfig } from '../getWorkflows';
import { mapWorkflowsToISOStringToRedux, mapWorkflowsAddComputedPropsToRedux } from '../../utils/mappers';
import { IWorkflow, IWorkflowClient, TWorkflowResponse } from '../../types/workflow';

const EXPORT_PAGE_LIMIT = 100;

export type TFetchAllWorkflowsParams = Omit<IGetWorkflowsConfig, 'offset' | 'limit'>;

function transformPageResults(response: { results: unknown[] }): IWorkflowClient[] {
  const resultsAsTsp = response.results as unknown as TWorkflowResponse[];
  const withDates = mapWorkflowsToISOStringToRedux(resultsAsTsp);
  return mapWorkflowsAddComputedPropsToRedux(withDates as IWorkflow[]);
}

/**
 * Fetches all workflows matching the given filters (all pages, no pagination limit).
 * Uses the same transformation as the workflows list (ISO dates + computed props).
 */
export async function fetchAllWorkflowsForExport(
  params: TFetchAllWorkflowsParams,
  pageLimit: number = EXPORT_PAGE_LIMIT,
): Promise<IWorkflowClient[]> {
  const first = await getWorkflows({ ...params, offset: 0, limit: pageLimit });
  const allResults = transformPageResults(first);

  if (first.results.length === 0 || allResults.length >= first.count) {
    return allResults;
  }

  const totalCount = first.count;
  const offsets = Array.from(
    { length: Math.ceil((totalCount - first.results.length) / pageLimit) },
    (_, i) => (i + 1) * pageLimit,
  );

  const rest = await offsets.reduce<Promise<IWorkflowClient[]>>(
    async (accPromise, offset) => {
      const acc = await accPromise;
      const next = await getWorkflows({ ...params, offset, limit: pageLimit });
      const page = transformPageResults(next);
      return [...acc, ...page];
    },
    Promise.resolve([]),
  );

  return [...allResults, ...rest];
}
