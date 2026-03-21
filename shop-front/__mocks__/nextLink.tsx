import React from 'react';

interface LinkProps {
  href: string;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  'aria-label'?: string;
}

export default function Link({ href, children, ...props }: LinkProps) {
  return (
    <a href={href} {...props}>
      {children}
    </a>
  );
}
