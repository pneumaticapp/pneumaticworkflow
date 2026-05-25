import { trackVideoEmbedding } from '../../../utils/analytics';
import {
  youtubeVideoRegexp,
  loomVideoRegexp,
  wistiaVideoRegexp,
} from '../../../constants/defaultValues';

export function trackVideoEmbeddingOnPaste(text: string): void {
  if (text.match(wistiaVideoRegexp)?.[0]) trackVideoEmbedding('Wistia');
  if (text.match(youtubeVideoRegexp)?.[0]) trackVideoEmbedding('YouTube');
  if (text.match(loomVideoRegexp)?.[0]) trackVideoEmbedding('Loom');
}
