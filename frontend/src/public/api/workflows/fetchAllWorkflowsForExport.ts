import { getWorkflows, IGetWorkflowsConfig } from '../getWorkflows';
import { mapWorkflowsToISOStringToRedux, mapWorkflowsAddComputedPropsToRedux } from '../../utils/mappers';
import { IWorkflow, IWorkflowClient, TWorkflowResponse } from '../../types/workflow';

const EXPORT_PAGE_LIMIT = 100;

export type TFetchAllWorkflowsParams = Omit<IGetWorkflowsConfig, 'offset' | 'limit'>;

/** Raw API response: results use timestamp fields (Tsp), not ISO strings */
interface IRawWorkflowsPageResponse {
  results: TWorkflowResponse[];
  count: number;
}

function transformPageResults(response: IRawWorkflowsPageResponse): IWorkflowClient[] {
  const withDates = mapWorkflowsToISOStringToRedux(response.results);
  return mapWorkflowsAddComputedPropsToRedux(withDates as IWorkflow[]);
}

function getRemainingOffsets(
  totalCount: number,
  firstPageLength: number,
  pageLimit: number,
): number[] {
  const remaining = totalCount - firstPageLength;
  if (remaining <= 0) return [];
  const pageCount = Math.ceil(remaining / pageLimit);
  return Array.from({ length: pageCount }, (_, i) => (i + 1) * pageLimit);
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
  const rawFirst = first as unknown as IRawWorkflowsPageResponse;
  const allResults = transformPageResults(rawFirst);

  if (rawFirst.results.length === 0 || allResults.length >= rawFirst.count) {
    return allResults;
  }

  const offsets = getRemainingOffsets(rawFirst.count, rawFirst.results.length, pageLimit);
  const restResults = await offsets.reduce<Promise<IWorkflowClient[]>>(
    async (accPromise, offset) => {
      const acc = await accPromise;
      const next = await getWorkflows({ ...params, offset, limit: pageLimit });
      const rawNext = next as unknown as IRawWorkflowsPageResponse;
      return [...acc, ...transformPageResults(rawNext)];
    },
    Promise.resolve([]),
  );

  return [...allResults, ...restResults];
}
