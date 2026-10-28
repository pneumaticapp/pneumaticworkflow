import { takeLatest } from 'redux-saga/effects';

import { loadHighlightsTemplatesTitles } from '../slice';
import { watchFetchTemplatesTitles } from '../saga';

describe('highlights saga', () => {
  it('keeps only the latest template titles request', () => {
    const saga = watchFetchTemplatesTitles();

    expect(saga.next().value).toEqual(takeLatest(loadHighlightsTemplatesTitles.type, expect.any(Function)));
  });
});
