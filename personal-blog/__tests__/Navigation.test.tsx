import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Navigation from '@/components/Navigation';

// next/link renders as <a> in tests
jest.mock('next/link', () => {
  return function MockLink({
    href,
    children,
    onClick,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    onClick?: () => void;
    [key: string]: unknown;
  }) {
    return (
      <a href={href} onClick={onClick} {...rest}>
        {children}
      </a>
    );
  };
});

describe('Navigation', () => {
  describe('nav links', () => {
    beforeEach(() => {
      render(<Navigation />);
    });

    it('renders Home link pointing to /', () => {
      const links = screen.getAllByRole('link', { name: '홈' });
      expect(links.length).toBeGreaterThan(0);
      links.forEach((link) => expect(link).toHaveAttribute('href', '/'));
    });

    it('renders Blog link pointing to /blog', () => {
      const links = screen.getAllByRole('link', { name: '블로그' });
      expect(links.length).toBeGreaterThan(0);
      links.forEach((link) => expect(link).toHaveAttribute('href', '/blog'));
    });

    it('renders Tags link pointing to /tags', () => {
      const links = screen.getAllByRole('link', { name: '태그' });
      expect(links.length).toBeGreaterThan(0);
      links.forEach((link) => expect(link).toHaveAttribute('href', '/tags'));
    });

    it('renders About link pointing to /about', () => {
      const links = screen.getAllByRole('link', { name: '소개' });
      expect(links.length).toBeGreaterThan(0);
      links.forEach((link) => expect(link).toHaveAttribute('href', '/about'));
    });

    it('renders site title link pointing to /', () => {
      const titleLink = screen.getByRole('link', { name: '개발 블로그' });
      expect(titleLink).toHaveAttribute('href', '/');
    });
  });

  describe('ThemeToggle inclusion', () => {
    it('renders a ThemeToggle button', () => {
      render(<Navigation />);
      // ThemeToggle renders a button with aria-label containing "모드로 전환"
      const toggleBtn = screen.getByRole('button', { name: /모드로 전환/ });
      expect(toggleBtn).toBeInTheDocument();
    });
  });

  describe('hamburger menu', () => {
    it('renders hamburger button with correct aria-label when closed', () => {
      render(<Navigation />);
      const btn = screen.getByTestId('hamburger-button');
      expect(btn).toHaveAttribute('aria-label', '메뉴 열기');
      expect(btn).toHaveAttribute('aria-expanded', 'false');
    });

    it('mobile menu is not visible initially', () => {
      render(<Navigation />);
      expect(screen.queryByTestId('mobile-menu')).not.toBeInTheDocument();
    });

    it('opens mobile menu on hamburger click', () => {
      render(<Navigation />);
      const btn = screen.getByTestId('hamburger-button');
      fireEvent.click(btn);
      expect(screen.getByTestId('mobile-menu')).toBeInTheDocument();
    });

    it('hamburger aria-label changes to "메뉴 닫기" when open', () => {
      render(<Navigation />);
      const btn = screen.getByTestId('hamburger-button');
      fireEvent.click(btn);
      expect(btn).toHaveAttribute('aria-label', '메뉴 닫기');
      expect(btn).toHaveAttribute('aria-expanded', 'true');
    });

    it('closes mobile menu on second hamburger click', () => {
      render(<Navigation />);
      const btn = screen.getByTestId('hamburger-button');
      fireEvent.click(btn);
      fireEvent.click(btn);
      expect(screen.queryByTestId('mobile-menu')).not.toBeInTheDocument();
    });

    it('mobile menu closes when a link is clicked', () => {
      render(<Navigation />);
      fireEvent.click(screen.getByTestId('hamburger-button'));
      // click any link in the mobile menu
      const mobileMenu = screen.getByTestId('mobile-menu');
      const firstLink = mobileMenu.querySelectorAll('a')[0];
      fireEvent.click(firstLink);
      expect(screen.queryByTestId('mobile-menu')).not.toBeInTheDocument();
    });

    it('mobile menu contains all four nav links', () => {
      render(<Navigation />);
      fireEvent.click(screen.getByTestId('hamburger-button'));
      const mobileMenu = screen.getByTestId('mobile-menu');
      expect(mobileMenu.querySelector('a[href="/"]')).toBeInTheDocument();
      expect(mobileMenu.querySelector('a[href="/blog"]')).toBeInTheDocument();
      expect(mobileMenu.querySelector('a[href="/tags"]')).toBeInTheDocument();
      expect(mobileMenu.querySelector('a[href="/about"]')).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('nav element has accessible label', () => {
      render(<Navigation />);
      expect(screen.getByRole('navigation', { name: '메인 내비게이션' })).toBeInTheDocument();
    });

    it('mobile menu has correct id for aria-controls', () => {
      render(<Navigation />);
      fireEvent.click(screen.getByTestId('hamburger-button'));
      expect(screen.getByTestId('mobile-menu')).toHaveAttribute('id', 'mobile-menu');
    });
  });
});
