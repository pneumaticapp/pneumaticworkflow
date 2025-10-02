/* eslint-disable */
/* prettier-ignore */
import { wistiaVideoRegexp, loomVideoRegexp, youtubeVideoRegexp } from '../../../constants/defaultValues';
import { trackVideoEmbedding } from '../../../utils/analytics';

enum EEmbeddedVideo {
  Wistia = 'Wistia',
  Loom = 'Loom',
  YouTube = 'YouTube',
}

export function trackAddVideo(text: string) {
  const trackFunctionMap = [
    {
      regExp: wistiaVideoRegexp,
      videoType: EEmbeddedVideo.Wistia,
    },
    {
      regExp: loomVideoRegexp,
      videoType: EEmbeddedVideo.Loom,
    },
    {
      regExp: youtubeVideoRegexp,
      videoType: EEmbeddedVideo.YouTube,
    },
  ];

  trackFunctionMap.forEach(({ regExp, videoType }) => {
    if (regExp.test(text)) {
      trackVideoEmbedding(videoType);
    }
  });
}
