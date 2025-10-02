import { getBrowserConfig } from '../../utils/getConfig';
import { IPagesStore } from '../../types/page';
import { EPagesActions, TPagesActions } from './actions';

const { pages } = getBrowserConfig();

const INIT_STATE: IPagesStore = {
  list: pages ? JSON.parse(String(pages)) : [],
};

// eslint-disable-next-line @typescript-eslint/default-param-last
export const reducer = (state = INIT_STATE, action: TPagesActions): IPagesStore => {
  switch (action.type) {
    case EPagesActions.LoadPagesSuccess:
      return { ...state, list: action.payload };
    default:
      return state;
  }
};
