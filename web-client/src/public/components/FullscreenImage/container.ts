/* eslint-disable */
/* prettier-ignore */
import { connect } from 'react-redux';
import { FullscreenImage, IFullscreenImageProps } from './FullscreenImage';
import { IApplicationState } from '../../types/redux';
import { closeFullscreenImage } from '../../redux/general/actions';

type TStoreProps = Pick<IFullscreenImageProps, 'url'>;
type TDispatchProps = Pick<IFullscreenImageProps, 'closeFullscreenImage'>;

export function mapStateToProps(
  { general: { fullscreenImage } }: IApplicationState,
): TStoreProps {
  return { url: fullscreenImage.url };
}

export const mapDispatchToProps: TDispatchProps = {
  closeFullscreenImage,
};

export const FullscreenImageContainer = connect(mapStateToProps, mapDispatchToProps)(FullscreenImage);
