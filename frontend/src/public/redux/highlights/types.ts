import { IGetHighlightsConfig } from '../../api/getHighlights';

export interface ILoadHighlightsConfig extends Omit<IGetHighlightsConfig, 'filters'> {
  onScroll?: boolean;
}
