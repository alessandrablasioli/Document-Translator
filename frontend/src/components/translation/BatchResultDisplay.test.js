import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import BatchResultDisplay from './BatchResultDisplay';
import { render } from '../../test-utils';

describe('BatchResultDisplay', () => {
  const mockOnReset = jest.fn();

  beforeEach(() => {
    mockOnReset.mockClear();
  });

  it('renders batch results table with file, status, download', () => {
    const results = [
      {
        original_file_id: 'id1',
        translated_file_id: 'trans1',
        status: 'completed',
      },
      {
        original_file_id: 'id2',
        status: 'failed',
        error: 'Could not extract text',
      },
    ];
    render(
      <BatchResultDisplay
        results={results}
        filenames={['doc1.txt', 'doc2.txt']}
        onReset={mockOnReset}
      />
    );

    expect(screen.getByRole('heading', { name: /translation completed/i })).toBeInTheDocument();
    expect(screen.getByText('doc1.txt')).toBeInTheDocument();
    expect(screen.getByText('doc2.txt')).toBeInTheDocument();
    expect(screen.getByText('Translation Complete!')).toBeInTheDocument();
    expect(screen.getByText(/could not extract text/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /download/i })).toHaveAttribute(
      'href',
      expect.stringContaining('/api/download/trans1')
    );
    expect(screen.getByRole('button', { name: /upload new file/i })).toBeInTheDocument();
  });

  it('calls onReset when Upload New File is clicked', () => {
    render(
      <BatchResultDisplay
        results={[{ original_file_id: 'id1', status: 'completed', translated_file_id: 't1' }]}
        onReset={mockOnReset}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /upload new file/i }));
    expect(mockOnReset).toHaveBeenCalled();
  });

  it('uses original_file_id when filenames not provided', () => {
    render(
      <BatchResultDisplay
        results={[{ original_file_id: 'abc-123', status: 'completed', translated_file_id: 't1' }]}
        onReset={mockOnReset}
      />
    );
    expect(screen.getByText('abc-123')).toBeInTheDocument();
  });
});
