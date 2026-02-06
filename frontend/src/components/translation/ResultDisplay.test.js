import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import ResultDisplay from './ResultDisplay';
import { render } from '../../test-utils';

describe('ResultDisplay', () => {
  const mockOnDownload = jest.fn();
  const mockOnReset = jest.fn();

  beforeEach(() => {
    mockOnDownload.mockClear();
    mockOnReset.mockClear();
  });

  it('renders success message and action buttons', () => {
    render(
      <ResultDisplay
        onDownload={mockOnDownload}
        onReset={mockOnReset}
        translatedFileId="test-file-123"
      />
    );
    expect(screen.getByText(/translation complete/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /download translated document/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /translate another document/i })).toBeInTheDocument();
  });

  it('renders download link with correct href when translatedFileId is provided', () => {
    render(
      <ResultDisplay
        onDownload={mockOnDownload}
        onReset={mockOnReset}
        translatedFileId="abc-456"
      />
    );
    const link = screen.getByRole('link', { name: /download translated document/i });
    expect(link).toHaveAttribute('href', expect.stringContaining('/api/download/abc-456'));
    expect(link).toHaveAttribute('download');
  });

  it('renders disabled download button when translatedFileId is missing', () => {
    render(<ResultDisplay onDownload={mockOnDownload} onReset={mockOnReset} />);
    const btn = screen.getByRole('button', { name: /download translated document/i });
    expect(btn).toBeDisabled();
  });

  it('calls onReset when Translate Another is clicked', () => {
    render(<ResultDisplay onDownload={mockOnDownload} onReset={mockOnReset} />);
    fireEvent.click(screen.getByRole('button', { name: /translate another document/i }));
    expect(mockOnReset).toHaveBeenCalled();
  });
});
