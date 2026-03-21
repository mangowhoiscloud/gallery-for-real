import React from 'react';

interface ImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  fill?: boolean;
  priority?: boolean;
  style?: React.CSSProperties;
}

export default function Image({ src, alt, width, height, fill: _fill, priority: _priority, ...props }: ImageProps) {
  return <img src={src} alt={alt} width={width} height={height} {...props} />;
}
