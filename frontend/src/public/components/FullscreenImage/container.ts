/* prettier-ignore */
import { connect } from 'react-redux';
import type { IFullscreenImageProps } from './FullscreenImage';
import { FullscreenImage } from './FullscreenImage';
import type { RootState } from '../../redux/store';
import { closeFullscreenImage } from '../../redux/general/actions';

type TStoreProps = Pick<IFullscreenImageProps, 'url'>;
type TDispatchProps = Pick<IFullscreenImageProps, 'closeFullscreenImage'>;

export function mapStateToProps({ general: { fullscreenImage } }: RootState): TStoreProps {
  return {
    url: fullscreenImage.url,
  };
}

export const mapDispatchToProps: TDispatchProps = {
  closeFullscreenImage,
};

export const FullscreenImageContainer = connect(mapStateToProps, mapDispatchToProps)(FullscreenImage);
