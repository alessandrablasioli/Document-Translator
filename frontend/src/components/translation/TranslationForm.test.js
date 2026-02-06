import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import TranslationForm from './TranslationForm';
import { render } from '../../test-utils';

describe('TranslationForm', () => {
  const mockOnTranslate = jest.fn();
  const mockOnReset = jest.fn();

  beforeEach(() => {
    mockOnTranslate.mockClear();
    mockOnReset.mockClear();
  });

  it('renders source/target language selects and translate button', () => {
    render(<TranslationForm onTranslate={mockOnTranslate} onReset={mockOnReset} />);
    expect(screen.getByLabelText(/source language/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/translate to/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /translate document/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload new file/i })).toBeInTheDocument();
  });

  it('calls onTranslate with target language and source (null when auto-detect) on submit', async () => {
    render(<TranslationForm onTranslate={mockOnTranslate} onReset={mockOnReset} />);
    const translateButton = screen.getByRole('button', { name: /translate document/i });
    fireEvent.click(translateButton);
    expect(mockOnTranslate).toHaveBeenCalledWith('English', null);
  });

  it('calls onReset when Upload New File is clicked', () => {
    render(<TranslationForm onTranslate={mockOnTranslate} onReset={mockOnReset} />);
    fireEvent.click(screen.getByRole('button', { name: /upload new file/i }));
    expect(mockOnReset).toHaveBeenCalled();
  });

  it('can change target language and submit', () => {
    render(<TranslationForm onTranslate={mockOnTranslate} onReset={mockOnReset} />);
    const select = screen.getByLabelText(/translate to/i);
    fireEvent.change(select, { target: { value: 'Spanish' } });
    fireEvent.click(screen.getByRole('button', { name: /translate document/i }));
    expect(mockOnTranslate).toHaveBeenCalledWith('Spanish', null);
  });

  it('shows Translate All button when isBatch is true', () => {
    render(<TranslationForm onTranslate={mockOnTranslate} onReset={mockOnReset} isBatch />);
    expect(screen.getByRole('button', { name: /translate all/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /translate document/i })).not.toBeInTheDocument();
  });
});
