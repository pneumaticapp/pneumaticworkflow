import { ETemplatesSorting } from '../../types/workflow';

const templatesTitlesByOwnersUrl = '/templates/titles-by-owners';
const templatesUrl = '/templates';

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: {
      urls: {
        templates: templatesUrl,
        templatesTitlesByOwners: templatesTitlesByOwnersUrl,
      },
    },
  }),
}));

import { commonRequest } from '../commonRequest';
import {
  getTemplates,
  getTemplatesByOwners,
  getTemplatesQueryString,
} from '../getTemplates';

jest.mock('../commonRequest');

describe('getTemplates', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls commonRequest with correct URL and default params', async () => {
    const mockResponse = { count: 1, results: [] };
    (commonRequest as jest.Mock).mockResolvedValueOnce(mockResponse);

    const result = await getTemplates({
      offset: 0,
      limit: 30,
      sorting: ETemplatesSorting.DateDesc,
    });

    expect(result).toEqual(mockResponse);
    expect(commonRequest).toHaveBeenCalledWith(
      `${templatesUrl}?limit=30&offset=0&ordering=-date`,
      {},
      { shouldThrow: true },
    );
  });

  it('includes search param when searchText provided', async () => {
    (commonRequest as jest.Mock).mockResolvedValueOnce({ count: 0, results: [] });

    await getTemplates({
      offset: 0,
      limit: 10,
      sorting: ETemplatesSorting.NameAsc,
      searchText: 'test',
    });

    expect(commonRequest).toHaveBeenCalledWith(
      `${templatesUrl}?limit=10&offset=0&search=test&ordering=name`,
      {},
      { shouldThrow: true },
    );
  });

  it('includes is_active param when isActive provided', async () => {
    (commonRequest as jest.Mock).mockResolvedValueOnce({ count: 0, results: [] });

    await getTemplates({
      offset: 0,
      limit: 10,
      sorting: ETemplatesSorting.DateDesc,
      isActive: true,
    });

    expect(commonRequest).toHaveBeenCalledWith(
      `${templatesUrl}?limit=10&offset=0&is_active=true&ordering=-date`,
      {},
      { shouldThrow: true },
    );
  });
});

describe('getTemplatesByOwners', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('calls commonRequest with titles-by-owners URL', async () => {
    const mockResponse = { count: 2, results: [{ id: 1 }, { id: 2 }] };
    (commonRequest as jest.Mock).mockResolvedValueOnce(mockResponse);

    const result = await getTemplatesByOwners({
      offset: 0,
      limit: 30,
      sorting: ETemplatesSorting.DateDesc,
    });

    expect(result).toEqual(mockResponse);
    expect(commonRequest).toHaveBeenCalledWith(
      `${templatesTitlesByOwnersUrl}?limit=30&offset=0&ordering=-date`,
      {},
      { shouldThrow: true },
    );
  });

  it('includes all query params correctly', async () => {
    (commonRequest as jest.Mock).mockResolvedValueOnce({ count: 0, results: [] });

    await getTemplatesByOwners({
      offset: 10,
      limit: 20,
      sorting: ETemplatesSorting.UsageDesc,
      searchText: 'workflow',
      isActive: false,
    });

    expect(commonRequest).toHaveBeenCalledWith(
      `${templatesTitlesByOwnersUrl}?limit=20&offset=10&is_active=false&search=workflow&ordering=-usage`,
      {},
      { shouldThrow: true },
    );
  });

  it('uses default sorting when not provided', async () => {
    (commonRequest as jest.Mock).mockResolvedValueOnce({ count: 0, results: [] });

    await getTemplatesByOwners({
      offset: 0,
      limit: 30,
    });

    expect(commonRequest).toHaveBeenCalledWith(
      `${templatesTitlesByOwnersUrl}?limit=30&offset=0&ordering=-date`,
      {},
      { shouldThrow: true },
    );
  });
});

describe('getTemplatesQueryString', () => {
  it('builds query string with all params', () => {
    const result = getTemplatesQueryString({
      limit: 30,
      offset: 0,
      sorting: ETemplatesSorting.DateDesc,
      searchText: 'test',
      isActive: true,
    });

    expect(result).toBe('limit=30&offset=0&is_active=true&search=test&ordering=-date');
  });

  it('excludes undefined limit and offset', () => {
    const result = getTemplatesQueryString({
      limit: undefined,
      offset: undefined,
      sorting: ETemplatesSorting.NameAsc,
      searchText: '',
      isActive: undefined,
    });

    expect(result).toBe('ordering=name');
  });

  it('handles all sorting options', () => {
    const sortingTests = [
      { sorting: ETemplatesSorting.DateAsc, expected: 'ordering=date' },
      { sorting: ETemplatesSorting.DateDesc, expected: 'ordering=-date' },
      { sorting: ETemplatesSorting.NameAsc, expected: 'ordering=name' },
      { sorting: ETemplatesSorting.NameDesc, expected: 'ordering=-name' },
      { sorting: ETemplatesSorting.UsageAsc, expected: 'ordering=usage' },
      { sorting: ETemplatesSorting.UsageDesc, expected: 'ordering=-usage' },
    ];

    sortingTests.forEach(({ sorting, expected }) => {
      const result = getTemplatesQueryString({
        limit: undefined,
        offset: undefined,
        sorting,
        searchText: '',
        isActive: undefined,
      });

      expect(result).toBe(expected);
    });
  });
});
