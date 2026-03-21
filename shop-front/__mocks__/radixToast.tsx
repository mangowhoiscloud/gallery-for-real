import React from 'react';

// Context so Root can pass its close handler to Close
const RootContext = React.createContext<{ close: () => void }>({ close: () => {} });

export const Provider = ({ children }: { children: React.ReactNode }) => <>{children}</>;

export const Viewport = ({ className }: { className?: string }) => (
  <div aria-label="Notifications" className={className} />
);

export const Root = ({
  children,
  defaultOpen,
  onOpenChange,
  className,
}: {
  children: React.ReactNode;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
}) => {
  const [isOpen, setIsOpen] = React.useState(defaultOpen !== false);
  const close = React.useCallback(() => {
    setIsOpen(false);
    onOpenChange?.(false);
  }, [onOpenChange]);
  if (!isOpen) return null;
  return (
    <RootContext.Provider value={{ close }}>
      <div role="status" className={className}>
        {children}
      </div>
    </RootContext.Provider>
  );
};

export const Title = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => <strong className={className}>{children}</strong>;

export const Description = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => <p className={className}>{children}</p>;

export const Close = ({
  children,
  className,
}: {
  children?: React.ReactNode;
  className?: string;
}) => {
  const { close } = React.useContext(RootContext);
  return (
    <button type="button" aria-label="close toast" className={className} onClick={close}>
      {children ?? '×'}
    </button>
  );
};

export const Action = ({
  children,
  className,
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  altText?: string;
  onClick?: () => void;
  asChild?: boolean;
}) => (
  <button type="button" className={className} onClick={onClick}>
    {children}
  </button>
);
