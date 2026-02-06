import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import LanguageSelector from './LanguageSelector';
import { render } from '../../test-utils';

describe('LanguageSelector', () => {
  it('renders current language code', () => {
    render(<LanguageSelector />);
    expect(screen.getByText('EN')).toBeInTheDocument();
  });

  it('opens dropdown when button is clicked', () => {
    render(<LanguageSelector />);
    fireEvent.click(screen.getByRole('button', { name: /change language/i }));
    expect(screen.getByText('English')).toBeInTheDocument();
    expect(screen.getByText('Español')).toBeInTheDocument();
  });

  it('changes language when option is selected', () => {
    render(<LanguageSelector />);
    fireEvent.click(screen.getByRole('button', { name: /change language/i }));
    fireEvent.click(screen.getByText('Español'));
    expect(screen.getByText('ES')).toBeInTheDocument();
  });
});
