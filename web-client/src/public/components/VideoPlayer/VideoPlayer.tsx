/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';

import ReactPlayer, { Config, SourceProps } from 'react-player';

export interface IVideoPlayerProps {
  url: string | string[] | SourceProps[] | MediaStream;
  height?: string | number;
  width?: string | number;
  playing?: boolean;
  loop?: boolean;
  light?: boolean | string;
  playerConfig?: Config;
}

export class VideoPlayer extends React.Component<IVideoPlayerProps> {

  public render() {
    const { url, playerConfig, ...rest } = this.props;

    return (
      <ReactPlayer url={url} {...rest}
        config={playerConfig}
      />
    );
  }
}
