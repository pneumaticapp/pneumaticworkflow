/* eslint-disable */
/* prettier-ignore */
import { RawDraftContentState } from 'draft-js';
import { normalizeDraftRaw } from '../normalizeDraftRaw';

describe('normalizeDraftRaw', () => {
  it('normalize correctly', () => {
    const initialRaw = {
      entityMap: {
        0: {
          type: 'image',
        },
        1: {
          type: 'image',
        },
      },
      blocks: [
        {
          depth: 0,
          type: 'unstyled',
          text: '11111\n \n2222\n ',
          entityRanges: [
            {
              offset: 6,
              length: 1,
              key: 0,
            },
            {
              offset: 13,
              length: 1,
              key: 1,
            },
          ],
          inlineStyleRanges: [],
        },
      ],
    };

    const expectedResult = {
      entityMap: { 0: { type: 'image' }, 1: { type: 'image' } },
      blocks: [
        {
          depth: 0,
          type: 'unstyled',
          entityRanges: [],
          inlineStyleRanges: [],
          text: '11111',
        },
        {
          depth: 0,
          type: 'atomic',
          entityRanges: [{
            offset: 0,
            length: 1,
            key: 0,
          }],
          inlineStyleRanges: [],
          text: ' ',
        },
        {
          depth: 0,
          type: 'unstyled',
          entityRanges: [],
          inlineStyleRanges: [],
          text: '',
        },
        {
          depth: 0,
          type: 'unstyled',
          entityRanges: [],
          inlineStyleRanges: [],
          text: '2222',
        },
        {
          depth: 0,
          type: 'atomic',
          entityRanges: [{
            offset: 0,
            length: 1,
            key: 1,
          }],
          inlineStyleRanges: [],
          text: ' ',
        },
      ],
    };

    expect(normalizeDraftRaw(initialRaw as unknown as RawDraftContentState)).toStrictEqual(expectedResult);
  });
});
