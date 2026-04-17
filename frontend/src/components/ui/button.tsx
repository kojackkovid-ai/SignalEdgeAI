import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost' | 'secondary';
  size?: 'default' | 'sm' | 'lg';
}

const buttonVariants = {
  default: 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800',
  outline: 'border border-gray-300 bg-white text-gray-950 hover:bg-gray-100 active:bg-gray-200',
  ghost: 'text-gray-950 hover:bg-gray-100 active:bg-gray-200',
  secondary: 'bg-gray-200 text-gray-950 hover:bg-gray-300 active:bg-gray-400',
};

const buttonSizes = {
  default: 'h-10 px-4 py-2 text-base',
  sm: 'h-8 px-3 py-1 text-sm',
  lg: 'h-12 px-8 py-2 text-lg',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className = '',
      variant = 'default',
      size = 'default',
      disabled = false,
      ...props
    },
    ref
  ) => (
    <button
      ref={ref}
      disabled={disabled}
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-md font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
        buttonVariants[variant]
      } ${buttonSizes[size]} ${className}`}
      {...props}
    />
  )
);
Button.displayName = 'Button';
