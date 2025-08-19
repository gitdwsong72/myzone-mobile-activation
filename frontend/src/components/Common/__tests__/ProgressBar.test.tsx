import React from 'react';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '../../../test-utils';
import ProgressBar from '../ProgressBar';

describe('ProgressBar Component', () => {
  test('기본 프로그레스 바가 올바르게 렌더링된다', () => {
    renderWithProviders(<ProgressBar value={50} max={100} />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
  });

  test('진행률이 올바르게 표시된다', () => {
    renderWithProviders(<ProgressBar value={75} max={100} showPercentage />);
    
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  test('라벨이 올바르게 표시된다', () => {
    renderWithProviders(
      <ProgressBar value={30} max={100} label="다운로드 진행률" />
    );
    
    expect(screen.getByText('다운로드 진행률')).toBeInTheDocument();
  });

  test('색상 variant가 올바르게 적용된다', () => {
    renderWithProviders(<ProgressBar value={50} max={100} variant="success" />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('progress-success');
  });

  test('크기가 올바르게 적용된다', () => {
    renderWithProviders(<ProgressBar value={50} max={100} size="large" />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('progress-large');
  });

  test('애니메이션이 활성화된다', () => {
    renderWithProviders(<ProgressBar value={50} max={100} animated />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('progress-animated');
  });

  test('스트라이프 패턴이 적용된다', () => {
    renderWithProviders(<ProgressBar value={50} max={100} striped />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('progress-striped');
  });

  test('0% 진행률이 올바르게 표시된다', () => {
    renderWithProviders(<ProgressBar value={0} max={100} showPercentage />);
    
    expect(screen.getByText('0%')).toBeInTheDocument();
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '0');
  });

  test('100% 진행률이 올바르게 표시된다', () => {
    renderWithProviders(<ProgressBar value={100} max={100} showPercentage />);
    
    expect(screen.getByText('100%')).toBeInTheDocument();
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
  });

  test('최대값을 초과하는 값이 제한된다', () => {
    renderWithProviders(<ProgressBar value={150} max={100} showPercentage />);
    
    expect(screen.getByText('100%')).toBeInTheDocument();
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
  });

  test('음수 값이 0으로 제한된다', () => {
    renderWithProviders(<ProgressBar value={-10} max={100} showPercentage />);
    
    expect(screen.getByText('0%')).toBeInTheDocument();
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '0');
  });

  test('커스텀 className이 추가된다', () => {
    renderWithProviders(
      <ProgressBar value={50} max={100} className="custom-progress" />
    );
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('progress-bar', 'custom-progress');
  });

  test('aria-label이 올바르게 설정된다', () => {
    renderWithProviders(
      <ProgressBar 
        value={50} 
        max={100} 
        aria-label="파일 업로드 진행률" 
      />
    );
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-label', '파일 업로드 진행률');
  });

  test('단계별 프로그레스 바가 올바르게 렌더링된다', () => {
    const steps = [
      { label: '1단계', completed: true },
      { label: '2단계', completed: true },
      { label: '3단계', completed: false },
      { label: '4단계', completed: false }
    ];
    
    renderWithProviders(<ProgressBar steps={steps} />);
    
    expect(screen.getByText('1단계')).toBeInTheDocument();
    expect(screen.getByText('2단계')).toBeInTheDocument();
    expect(screen.getByText('3단계')).toBeInTheDocument();
    expect(screen.getByText('4단계')).toBeInTheDocument();
    
    // 완료된 단계는 completed 클래스를 가져야 함
    const step1 = screen.getByText('1단계').closest('.step');
    const step2 = screen.getByText('2단계').closest('.step');
    const step3 = screen.getByText('3단계').closest('.step');
    const step4 = screen.getByText('4단계').closest('.step');
    
    expect(step1).toHaveClass('step-completed');
    expect(step2).toHaveClass('step-completed');
    expect(step3).not.toHaveClass('step-completed');
    expect(step4).not.toHaveClass('step-completed');
  });

  test('현재 단계가 올바르게 표시된다', () => {
    const steps = [
      { label: '1단계', completed: true },
      { label: '2단계', completed: false, current: true },
      { label: '3단계', completed: false }
    ];
    
    renderWithProviders(<ProgressBar steps={steps} />);
    
    const currentStep = screen.getByText('2단계').closest('.step');
    expect(currentStep).toHaveClass('step-current');
  });

  test('인디터미네이트 상태가 올바르게 표시된다', () => {
    renderWithProviders(<ProgressBar indeterminate />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('progress-indeterminate');
    expect(progressBar).not.toHaveAttribute('aria-valuenow');
  });

  test('버퍼 진행률이 올바르게 표시된다', () => {
    renderWithProviders(
      <ProgressBar value={30} max={100} bufferValue={60} />
    );
    
    const progressBar = screen.getByRole('progressbar');
    const bufferBar = progressBar.querySelector('.progress-buffer');
    expect(bufferBar).toBeInTheDocument();
  });
});