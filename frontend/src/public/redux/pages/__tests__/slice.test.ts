import { IPage } from '../types';

const mockPages: IPage[] = [{ slug: 'about', title: 'About', description: 'About us' }];

function loadInitialList(pages?: unknown) {
  jest.resetModules();
  Object.assign(window, { __pneumaticConfig: { pages } });

  const { default: pagesReducer }: typeof import('../slice') = require('../slice');

  return pagesReducer(undefined, { type: 'unknown' }).list;
}

describe('pages slice', () => {
  describe('initial state', () => {
    it('sets empty array when pages from browser config is an empty array', () => {
      expect(loadInitialList([])).toEqual([]);
    });

    it('sets pages list when pages from browser config is an array of pages', () => {
      expect(loadInitialList(mockPages)).toEqual(mockPages);
    });

    it('falls back to empty array when pages in browser config is null or undefined', () => {
      expect(loadInitialList(null)).toEqual([]);
      expect(loadInitialList(undefined)).toEqual([]);
    });
  });
});
