import { takeLatest } from 'redux-saga/effects';

import { EHighlightsActions } from '../actions';
import { watchFetchTemplatesTitles } from '../saga';

describe('highlights saga', () => {
  it('keeps only the latest template titles request', () => {
    const saga = watchFetchTemplatesTitles();

    expect(saga.next().value).toEqual(
      takeLatest(EHighlightsActions.LoadHighlightsTemplatesTitles, expect.any(Function)),
    );
  });
});
