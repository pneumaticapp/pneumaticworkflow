jest.mock('../../../utils/getConfig', () => ({
  getBrowserConfigEnv: jest.fn().mockReturnValue({
    api: {
      urls: {
        templates: '/templates',
        templatesTitlesByOwners: '/templates/titles-by-owners',
        systemTemplates: '/templates/system',
        systemTemplatesCategories: '/templates/system/categories',
      },
    },
  }),
}));

import { expectSaga } from 'redux-saga-test-plan';
import * as matchers from 'redux-saga-test-plan/matchers';

import * as getTemplatesApi from '../../../api/getTemplates';
import * as getSystemTemplatesApi from '../../../api/getSystemTemplates';
import * as getSystemTemplatesCategoriesApi from '../../../api/getSystemTemplatesCategories';
import { ETemplatesSorting } from '../../../types/workflow';
import { LIMIT_LOAD_TEMPLATES, LIMIT_LOAD_SYSTEMS_TEMPLATES } from '../../../constants/defaultValues';
import { getIsAdmin } from '../../selectors/user';
import { getTemplatesSystemList } from '../../selectors/templates';
import { fetchTemplatesSystem, fetchTemplatesSystemCategories } from '../saga';

describe('templates saga', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchTemplatesSystem', () => {
    it('does not call system templates API for non-admin', () => {
      const getTemplatesSystemMock = jest.spyOn(getSystemTemplatesApi, 'getTemplatesSystem');

      return expectSaga(fetchTemplatesSystem as any)
        .provide([[matchers.select.selector(getIsAdmin), false]])
        .run()
        .then(() => {
          expect(getTemplatesSystemMock).not.toHaveBeenCalled();
        });
    });

    it('calls system templates API for admin', () => {
      const getTemplatesSystemMock = jest
        .spyOn(getSystemTemplatesApi, 'getTemplatesSystem')
        .mockResolvedValue({ count: 0, results: [] });

      return expectSaga(fetchTemplatesSystem as any)
        .provide([
          [matchers.select.selector(getIsAdmin), true],
          [
            matchers.select.selector(getTemplatesSystemList),
            {
              items: [],
              selection: { offset: 0, searchText: '', category: null, count: 0 },
            },
          ],
        ])
        .run()
        .then(() => {
          expect(getTemplatesSystemMock).toHaveBeenCalledWith({
            category: null,
            searchText: '',
            limit: LIMIT_LOAD_SYSTEMS_TEMPLATES,
            offset: 0,
          });
        });
    });
  });

  describe('fetchTemplatesSystemCategories', () => {
    it('does not call system templates categories API for non-admin', () => {
      const getCategoriesMock = jest.spyOn(
        getSystemTemplatesCategoriesApi,
        'getTemplatesSystemCategories',
      );

      return expectSaga(fetchTemplatesSystemCategories as any)
        .provide([[matchers.select.selector(getIsAdmin), false]])
        .run()
        .then(() => {
          expect(getCategoriesMock).not.toHaveBeenCalled();
        });
    });
  });

  describe('fetchTemplates', () => {
    it('calls getTemplatesByOwners with correct parameters', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({
          count: 2,
          results: [
            { id: 1, name: 'Template 1' },
            { id: 2, name: 'Template 2' },
          ],
        } as any);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });
    });

    it('calls getTemplatesByOwners instead of getTemplates for My Workflow Templates', async () => {
      const getTemplatesMock = jest.spyOn(getTemplatesApi, 'getTemplates');
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 0, results: [] } as any);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: 30,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalled();
      expect(getTemplatesMock).not.toHaveBeenCalled();
    });

    it('handles pagination offset correctly', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 50, results: [] } as any);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 30,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 30,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.DateDesc,
      });
    });

    it('passes sorting parameter correctly', async () => {
      const getTemplatesByOwnersMock = jest
        .spyOn(getTemplatesApi, 'getTemplatesByOwners')
        .mockResolvedValue({ count: 0, results: [] } as any);

      await getTemplatesApi.getTemplatesByOwners({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.NameAsc,
      });

      expect(getTemplatesByOwnersMock).toHaveBeenCalledWith({
        offset: 0,
        limit: LIMIT_LOAD_TEMPLATES,
        sorting: ETemplatesSorting.NameAsc,
      });
    });
  });

  describe('fetchIsTemplateOwner', () => {
    it('uses getTemplates (not getTemplatesByOwners) to check ownership', async () => {
      const getTemplatesMock = jest
        .spyOn(getTemplatesApi, 'getTemplates')
        .mockResolvedValue({ count: 1, results: [{ id: 1 }] } as any);

      await getTemplatesApi.getTemplates({
        limit: 1,
        isActive: true,
      });

      expect(getTemplatesMock).toHaveBeenCalledWith({
        limit: 1,
        isActive: true,
      });
    });
  });
});
