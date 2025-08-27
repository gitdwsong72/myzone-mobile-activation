#!/usr/bin/env node

/**
 * 성능 분석 스크립트
 * 빌드 후 번들 크기, 청크 분석 등을 수행합니다.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const BUILD_DIR = path.join(__dirname, '../build');
const STATIC_DIR = path.join(BUILD_DIR, 'static');

// 파일 크기 포맷팅
function formatSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 디렉토리 크기 계산
function getDirectorySize(dirPath) {
  if (!fs.existsSync(dirPath)) return 0;
  
  let totalSize = 0;
  const files = fs.readdirSync(dirPath);
  
  files.forEach(file => {
    const filePath = path.join(dirPath, file);
    const stats = fs.statSync(filePath);
    
    if (stats.isDirectory()) {
      totalSize += getDirectorySize(filePath);
    } else {
      totalSize += stats.size;
    }
  });
  
  return totalSize;
}

// 파일 목록과 크기 가져오기
function getFilesWithSizes(dirPath, extension) {
  if (!fs.existsSync(dirPath)) return [];
  
  const files = [];
  const items = fs.readdirSync(dirPath);
  
  items.forEach(item => {
    const itemPath = path.join(dirPath, item);
    const stats = fs.statSync(itemPath);
    
    if (stats.isFile() && item.endsWith(extension)) {
      files.push({
        name: item,
        size: stats.size,
        path: itemPath
      });
    }
  });
  
  return files.sort((a, b) => b.size - a.size);
}

// 성능 분석 실행
function analyzePerformance() {
  console.log('📊 성능 분석을 시작합니다...\n');
  
  if (!fs.existsSync(BUILD_DIR)) {
    console.error('❌ 빌드 디렉토리를 찾을 수 없습니다. 먼저 빌드를 실행하세요.');
    process.exit(1);
  }
  
  // 전체 빌드 크기
  const totalSize = getDirectorySize(BUILD_DIR);
  console.log(`📦 전체 빌드 크기: ${formatSize(totalSize)}`);
  
  // JavaScript 파일 분석
  const jsDir = path.join(STATIC_DIR, 'js');
  const jsFiles = getFilesWithSizes(jsDir, '.js');
  const jsSize = jsFiles.reduce((sum, file) => sum + file.size, 0);
  
  console.log(`\n🟨 JavaScript 파일 (총 ${formatSize(jsSize)}):`);
  jsFiles.forEach(file => {
    const isChunk = file.name.includes('.chunk.');
    const isMain = file.name.includes('main.');
    const type = isMain ? '[메인]' : isChunk ? '[청크]' : '[기타]';
    console.log(`  ${type} ${file.name}: ${formatSize(file.size)}`);
  });
  
  // CSS 파일 분석
  const cssDir = path.join(STATIC_DIR, 'css');
  const cssFiles = getFilesWithSizes(cssDir, '.css');
  const cssSize = cssFiles.reduce((sum, file) => sum + file.size, 0);
  
  console.log(`\n🟦 CSS 파일 (총 ${formatSize(cssSize)}):`);
  cssFiles.forEach(file => {
    const isChunk = file.name.includes('.chunk.');
    const isMain = file.name.includes('main.');
    const type = isMain ? '[메인]' : isChunk ? '[청크]' : '[기타]';
    console.log(`  ${type} ${file.name}: ${formatSize(file.size)}`);
  });
  
  // 미디어 파일 분석
  const mediaDir = path.join(STATIC_DIR, 'media');
  if (fs.existsSync(mediaDir)) {
    const mediaSize = getDirectorySize(mediaDir);
    console.log(`\n🟩 미디어 파일: ${formatSize(mediaSize)}`);
  }
  
  // 성능 권장사항
  console.log('\n💡 성능 권장사항:');
  
  const recommendations = [];
  
  // 전체 크기 검사
  if (totalSize > 2 * 1024 * 1024) { // 2MB
    recommendations.push('전체 빌드 크기가 2MB를 초과합니다. 코드 스플리팅을 고려하세요.');
  }
  
  // JavaScript 크기 검사
  if (jsSize > 1024 * 1024) { // 1MB
    recommendations.push('JavaScript 번들이 1MB를 초과합니다. 동적 임포트를 사용하세요.');
  }
  
  // 큰 개별 파일 검사
  jsFiles.forEach(file => {
    if (file.size > 500 * 1024) { // 500KB
      recommendations.push(`${file.name} 파일이 500KB를 초과합니다. 분할을 고려하세요.`);
    }
  });
  
  // CSS 크기 검사
  if (cssSize > 100 * 1024) { // 100KB
    recommendations.push('CSS 번들이 100KB를 초과합니다. 사용하지 않는 스타일을 제거하세요.');
  }
  
  if (recommendations.length === 0) {
    recommendations.push('번들 크기가 적절합니다. 좋은 성능을 유지하고 있습니다!');
  }
  
  recommendations.forEach((rec, index) => {
    console.log(`  ${index + 1}. ${rec}`);
  });
  
  // 성능 점수 계산
  let score = 100;
  
  if (totalSize > 3 * 1024 * 1024) score -= 30; // 3MB 초과
  else if (totalSize > 2 * 1024 * 1024) score -= 15; // 2MB 초과
  
  if (jsSize > 1.5 * 1024 * 1024) score -= 25; // 1.5MB 초과
  else if (jsSize > 1024 * 1024) score -= 10; // 1MB 초과
  
  if (cssSize > 150 * 1024) score -= 15; // 150KB 초과
  else if (cssSize > 100 * 1024) score -= 5; // 100KB 초과
  
  score = Math.max(0, score);
  
  const grade = score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F';
  
  console.log(`\n🏆 성능 점수: ${score}/100 (${grade}등급)`);
  
  // 결과를 JSON 파일로 저장
  const analysisResult = {
    timestamp: new Date().toISOString(),
    totalSize,
    jsSize,
    cssSize,
    mediaSize: fs.existsSync(mediaDir) ? getDirectorySize(mediaDir) : 0,
    files: {
      js: jsFiles,
      css: cssFiles
    },
    score,
    grade,
    recommendations
  };
  
  const reportPath = path.join(BUILD_DIR, 'performance-analysis.json');
  fs.writeFileSync(reportPath, JSON.stringify(analysisResult, null, 2));
  console.log(`\n📄 상세 분석 결과가 ${reportPath}에 저장되었습니다.`);
  
  // 임계값 초과 시 경고 종료 코드
  if (score < 70) {
    console.log('\n⚠️ 성능 점수가 70점 미만입니다. 최적화가 필요합니다.');
    process.exit(1);
  }
  
  console.log('\n✅ 성능 분석이 완료되었습니다.');
}

// 스크립트 실행
if (require.main === module) {
  analyzePerformance();
}

module.exports = { analyzePerformance, formatSize, getDirectorySize };