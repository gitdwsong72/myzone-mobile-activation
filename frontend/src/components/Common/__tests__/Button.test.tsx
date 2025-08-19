import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '../../../test-utils';
import Button from '../Button';

describe('Button Component', () => {
  test('기본 버튼이 올바르게 렌더링된다', () => {
    renderWithProviders(<Button>클릭하세요</Button>);
    
    const button = screen.getByRole('button', { name: '클릭하세요' });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('btn');
  });

  test('primary 버튼 스타일이 적용된다', () => {
    renderWithProviders(<Button variant="primary">Primary 버튼</Button>);
    
    const button = screen.getByRole('button', { name: 'Primary 버튼' });
    expect(button).toHaveClass('btn-primary');
  });

  test('secondary 버튼 스타일이 적용된다', () => {
    renderWithProviders(<Button variant="secondary">Secondary 버튼</Button>);
    
    const button = screen.getByRole('button', { name: 'Secondary 버튼' });
    expect(button).toHaveClass('btn-secondary');
  });

  test('disabled 상태가 올바르게 적용된다', () => {
    renderWithProviders(<Button disabled>비활성 버튼</Button>);
    
    const button = screen.getByRole('button', { name: '비활성 버튼' });
    expect(button).toBeDisabled();
    expect(button).toHaveClass('btn-disabled');
  });

  test('loading 상태가 올바르게 표시된다', () => {
    renderWithProviders(<Button loading>로딩 버튼</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByText('로딩 중...')).toBeInTheDocument();
  });

  test('클릭 이벤트가 올바르게 처리된다', () => {
    const handleClick = jest.fn();
    renderWithProviders(<Button onClick={handleClick}>클릭 테스트</Button>);
    
    const button = screen.getByRole('button', { name: '클릭 테스트' });
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  test('disabled 상태에서는 클릭 이벤트가 발생하지 않는다', () => {
    const handleClick = jest.fn();
    renderWithProviders(
      <Button onClick={handleClick} disabled>
        비활성 버튼
      </Button>
    );
    
    const button = screen.getByRole('button', { name: '비활성 버튼' });
    fireEvent.click(button);
    
    expect(handleClick).not.toHaveBeenCalled();
  });

  test('loading 상태에서는 클릭 이벤트가 발생하지 않는다', () => {
    const handleClick = jest.fn();
    renderWithProviders(
      <Button onClick={handleClick} loading>
        로딩 버튼
      </Button>
    );
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(handleClick).not.toHaveBeenCalled();
  });

  test('size prop이 올바르게 적용된다', () => {
    renderWithProviders(<Button size="large">큰 버튼</Button>);
    
    const button = screen.getByRole('button', { name: '큰 버튼' });
    expect(button).toHaveClass('btn-large');
  });

  test('fullWidth prop이 올바르게 적용된다', () => {
    renderWithProviders(<Button fullWidth>전체 너비 버튼</Button>);
    
    const button = screen.getByRole('button', { name: '전체 너비 버튼' });
    expect(button).toHaveClass('btn-full-width');
  });

  test('커스텀 className이 추가된다', () => {
    renderWithProviders(
      <Button className="custom-class">커스텀 버튼</Button>
    );
    
    const button = screen.getByRole('button', { name: '커스텀 버튼' });
    expect(button).toHaveClass('btn', 'custom-class');
  });

  test('type prop이 올바르게 설정된다', () => {
    renderWithProviders(<Button type="submit">제출 버튼</Button>);
    
    const button = screen.getByRole('button', { name: '제출 버튼' });
    expect(button).toHaveAttribute('type', 'submit');
  });

  test('아이콘과 텍스트가 함께 표시된다', () => {
    const icon = <span data-testid="icon">🔍</span>;
    renderWithProviders(
      <Button icon={icon}>검색</Button>
    );
    
    expect(screen.getByTestId('icon')).toBeInTheDocument();
    expect(screen.getByText('검색')).toBeInTheDocument();
  });

  test('아이콘만 있는 버튼이 올바르게 렌더링된다', () => {
    const icon = <span data-testid="icon">❌</span>;
    renderWithProviders(<Button icon={icon} />);
    
    expect(screen.getByTestId('icon')).toBeInTheDocument();
    expect(screen.getByRole('button')).toHaveClass('btn-icon-only');
  });
});