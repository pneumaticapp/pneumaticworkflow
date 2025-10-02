/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { IVideoPlayerProps, VideoPlayer } from './VideoPlayer';
import { DEFAULT_VIDEO_PLAYER_CONFIG } from '../../constants/defaultValues';

export function mapStateToProps(): IVideoPlayerProps {
  return {
    url: '',
    height: '100%',
    width: '100%',
    playing: false,
    loop: false,
    light: false,
    playerConfig: DEFAULT_VIDEO_PLAYER_CONFIG,
  };
}

export const VideoPlayerContainer = connect<IVideoPlayerProps>(mapStateToProps)(VideoPlayer);
