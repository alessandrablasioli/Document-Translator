import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import FileUpload from './FileUpload';
import { render } from '../../test-utils';

// Mock window.alert so we can assert on it
const alertMock = jest.spyOn(window, 'alert').mockImplementation(() => {});

describe('FileUpload', () => {
  const mockOnFileUpload = jest.fn();

  beforeEach(() => {
    mockOnFileUpload.mockClear();
    alertMock.mockClear();
  });

  afterAll(() => {
    alertMock.mockRestore();
  });

  it('renders upload title and description', () => {
    render(<FileUpload onFileUpload={mockOnFileUpload} />);
    expect(screen.getByText(/upload document/i)).toBeInTheDocument();
    expect(screen.getByText(/drag and drop/i)).toBeInTheDocument();
  });

  it('calls onFileUpload when a supported file is selected', () => {
    const { container } = render(<FileUpload onFileUpload={mockOnFileUpload} />);
    const input = container.querySelector('input[type="file"]');
    const file = new File(['content'], 'document.txt', { type: 'text/plain' });
    fireEvent.change(input, { target: { files: [file] } });
    expect(mockOnFileUpload).toHaveBeenCalledWith(file);
  });

  it('shows alert when unsupported file type is selected', () => {
    const { container } = render(<FileUpload onFileUpload={mockOnFileUpload} />);
    const input = container.querySelector('input[type="file"]');
    const file = new File(['content'], 'file.csv', { type: 'text/csv' });
    fireEvent.change(input, { target: { files: [file] } });
    expect(mockOnFileUpload).not.toHaveBeenCalled();
    expect(alertMock).toHaveBeenCalledWith(expect.stringContaining('Unsupported'));
  });

  it('calls onFilesUpload with array when multiple files selected and onFilesUpload provided', () => {
    const mockOnFilesUpload = jest.fn();
    const { container } = render(
      <FileUpload onFileUpload={mockOnFileUpload} onFilesUpload={mockOnFilesUpload} />
    );
    const input = container.querySelector('input[type="file"]');
    const file1 = new File(['a'], 'a.txt', { type: 'text/plain' });
    const file2 = new File(['b'], 'b.txt', { type: 'text/plain' });
    fireEvent.change(input, { target: { files: [file1, file2] } });
    expect(mockOnFilesUpload).toHaveBeenCalledTimes(1);
    expect(mockOnFilesUpload).toHaveBeenCalledWith([file1, file2]);
    expect(mockOnFileUpload).not.toHaveBeenCalled();
  });

  it('calls onFileUpload with single file when one file selected even if onFilesUpload provided', () => {
    const mockOnFilesUpload = jest.fn();
    const { container } = render(
      <FileUpload onFileUpload={mockOnFileUpload} onFilesUpload={mockOnFilesUpload} />
    );
    const input = container.querySelector('input[type="file"]');
    const file = new File(['x'], 'single.txt', { type: 'text/plain' });
    fireEvent.change(input, { target: { files: [file] } });
    expect(mockOnFileUpload).toHaveBeenCalledWith(file);
    expect(mockOnFilesUpload).not.toHaveBeenCalled();
  });
});
