import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '../../../test-utils';
import Modal from '../Modal';

describe('Modal Component', () => {
  test('모달이 열린 상태에서 올바르게 렌더링된다', () => {
    renderWithProviders(
      <Modal isOpen={true} onClose={jest.fn()} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('테스트 모달')).toBeInTheDocument();
    expect(screen.getByText('모달 내용입니다.')).toBeInTheDocument();
  });

  test('모달이 닫힌 상태에서는 렌더링되지 않는다', () => {
    renderWithProviders(
      <Modal isOpen={false} onClose={jest.fn()} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(screen.queryByText('테스트 모달')).not.toBeInTheDocument();
  });

  test('닫기 버튼 클릭 시 onClose가 호출된다', () => {
    const handleClose = jest.fn();
    renderWithProviders(
      <Modal isOpen={true} onClose={handleClose} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    const closeButton = screen.getByRole('button', { name: /닫기/i });
    fireEvent.click(closeButton);
    
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  test('오버레이 클릭 시 onClose가 호출된다', () => {
    const handleClose = jest.fn();
    renderWithProviders(
      <Modal isOpen={true} onClose={handleClose} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    const overlay = screen.getByTestId('modal-overlay');
    fireEvent.click(overlay);
    
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  test('모달 콘텐츠 클릭 시 onClose가 호출되지 않는다', () => {
    const handleClose = jest.fn();
    renderWithProviders(
      <Modal isOpen={true} onClose={handleClose} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    const modalContent = screen.getByTestId('modal-content');
    fireEvent.click(modalContent);
    
    expect(handleClose).not.toHaveBeenCalled();
  });

  test('ESC 키 누를 시 onClose가 호출된다', () => {
    const handleClose = jest.fn();
    renderWithProviders(
      <Modal isOpen={true} onClose={handleClose} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  test('closeOnOverlayClick이 false일 때 오버레이 클릭으로 닫히지 않는다', () => {
    const handleClose = jest.fn();
    renderWithProviders(
      <Modal 
        isOpen={true} 
        onClose={handleClose} 
        title="테스트 모달"
        closeOnOverlayClick={false}
      >
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    const overlay = screen.getByTestId('modal-overlay');
    fireEvent.click(overlay);
    
    expect(handleClose).not.toHaveBeenCalled();
  });

  test('closeOnEsc가 false일 때 ESC 키로 닫히지 않는다', () => {
    const handleClose = jest.fn();
    renderWithProviders(
      <Modal 
        isOpen={true} 
        onClose={handleClose} 
        title="테스트 모달"
        closeOnEsc={false}
      >
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    
    expect(handleClose).not.toHaveBeenCalled();
  });

  test('size prop이 올바르게 적용된다', () => {
    renderWithProviders(
      <Modal isOpen={true} onClose={jest.fn()} title="큰 모달" size="large">
        <p>큰 모달 내용입니다.</p>
      </Modal>
    );
    
    const modalContent = screen.getByTestId('modal-content');
    expect(modalContent).toHaveClass('modal-large');
  });

  test('footer가 올바르게 렌더링된다', () => {
    const footer = (
      <div>
        <button>취소</button>
        <button>확인</button>
      </div>
    );
    
    renderWithProviders(
      <Modal isOpen={true} onClose={jest.fn()} title="테스트 모달" footer={footer}>
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    expect(screen.getByText('취소')).toBeInTheDocument();
    expect(screen.getByText('확인')).toBeInTheDocument();
  });

  test('showCloseButton이 false일 때 닫기 버튼이 표시되지 않는다', () => {
    renderWithProviders(
      <Modal 
        isOpen={true} 
        onClose={jest.fn()} 
        title="테스트 모달"
        showCloseButton={false}
      >
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    expect(screen.queryByRole('button', { name: /닫기/i })).not.toBeInTheDocument();
  });

  test('모달이 열릴 때 body에 overflow hidden이 적용된다', () => {
    renderWithProviders(
      <Modal isOpen={true} onClose={jest.fn()} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    expect(document.body.style.overflow).toBe('hidden');
  });

  test('모달이 닫힐 때 body의 overflow가 복원된다', () => {
    const { rerender } = renderWithProviders(
      <Modal isOpen={true} onClose={jest.fn()} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    expect(document.body.style.overflow).toBe('hidden');
    
    rerender(
      <Modal isOpen={false} onClose={jest.fn()} title="테스트 모달">
        <p>모달 내용입니다.</p>
      </Modal>
    );
    
    expect(document.body.style.overflow).toBe('');
  });

  test('포커스 트랩이 올바르게 작동한다', () => {
    renderWithProviders(
      <Modal isOpen={true} onClose={jest.fn()} title="테스트 모달">
        <input data-testid="input1" />
        <input data-testid="input2" />
      </Modal>
    );
    
    const input1 = screen.getByTestId('input1');
    const input2 = screen.getByTestId('input2');
    const closeButton = screen.getByRole('button', { name: /닫기/i });
    
    // 첫 번째 포커스 가능한 요소에 포커스가 있어야 함
    expect(input1).toHaveFocus();
    
    // Tab 키로 다음 요소로 이동
    fireEvent.keyDown(input1, { key: 'Tab' });
    expect(input2).toHaveFocus();
    
    // 마지막 요소에서 Tab 키를 누르면 첫 번째 요소로 이동
    fireEvent.keyDown(closeButton, { key: 'Tab' });
    expect(input1).toHaveFocus();
  });
});