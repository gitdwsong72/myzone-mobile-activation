import React, { useState, useEffect } from 'react';
import './SupportPage.css';
import LoadingSpinner from '../../components/Common/LoadingSpinner';

interface FAQ {
  id: number;
  category: string;
  question: string;
  answer: string;
  view_count: number;
}

interface InquiryForm {
  name: string;
  email: string;
  phone: string;
  order_number: string;
  category: string;
  subject: string;
  content: string;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
}

const SupportPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'faq' | 'inquiry' | 'chat'>('faq');
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [filteredFaqs, setFilteredFaqs] = useState<FAQ[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [inquirySubmitted, setInquirySubmitted] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');

  const [inquiryForm, setInquiryForm] = useState<InquiryForm>({
    name: '',
    email: '',
    phone: '',
    order_number: '',
    category: '',
    subject: '',
    content: ''
  });

  const [formErrors, setFormErrors] = useState<Partial<InquiryForm>>({});

  const inquiryCategories = [
    '요금제', '개통절차', '결제', '배송', '단말기', '번호', '기타'
  ];

  // FAQ 데이터 로드
  useEffect(() => {
    loadFaqs();
  }, []);

  // FAQ 필터링
  useEffect(() => {
    let filtered = faqs;

    if (selectedCategory) {
      filtered = filtered.filter(faq => faq.category === selectedCategory);
    }

    if (searchTerm) {
      filtered = filtered.filter(faq => 
        faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredFaqs(filtered);
  }, [faqs, selectedCategory, searchTerm]);

  const loadFaqs = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/support/faqs');
      if (response.ok) {
        const data = await response.json();
        setFaqs(data.faqs);
        setCategories(data.categories);
      }
    } catch (error) {
      console.error('FAQ 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFaqClick = async (faqId: number) => {
    if (expandedFaq === faqId) {
      setExpandedFaq(null);
    } else {
      setExpandedFaq(faqId);
      // 조회수 증가를 위해 상세 조회 API 호출
      try {
        await fetch(`/api/v1/support/faqs/${faqId}`);
      } catch (error) {
        console.error('FAQ 조회 실패:', error);
      }
    }
  };

  const validateInquiryForm = (): boolean => {
    const errors: Partial<InquiryForm> = {};

    if (!inquiryForm.name.trim()) errors.name = '이름을 입력해주세요.';
    if (!inquiryForm.email.trim()) errors.email = '이메일을 입력해주세요.';
    if (!inquiryForm.category) errors.category = '문의 유형을 선택해주세요.';
    if (!inquiryForm.subject.trim()) errors.subject = '제목을 입력해주세요.';
    if (!inquiryForm.content.trim()) errors.content = '문의 내용을 입력해주세요.';

    // 이메일 형식 검증
    if (inquiryForm.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inquiryForm.email)) {
      errors.email = '올바른 이메일 형식을 입력해주세요.';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInquirySubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateInquiryForm()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/support/inquiries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(inquiryForm),
      });

      if (response.ok) {
        setInquirySubmitted(true);
        setInquiryForm({
          name: '',
          email: '',
          phone: '',
          order_number: '',
          category: '',
          subject: '',
          content: ''
        });
      } else {
        throw new Error('문의 접수에 실패했습니다.');
      }
    } catch (error) {
      console.error('문의 접수 실패:', error);
      alert('문의 접수에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleChatSend = () => {
    if (!chatInput.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: chatInput,
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');

    // 간단한 챗봇 응답 시뮬레이션
    setTimeout(() => {
      const botResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: getBotResponse(chatInput),
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, botResponse]);
    }, 1000);
  };

  const getBotResponse = (input: string): string => {
    const lowerInput = input.toLowerCase();
    
    if (lowerInput.includes('요금제')) {
      return '요금제 관련 문의시네요. 5G와 LTE 요금제를 제공하고 있으며, 자세한 내용은 FAQ를 확인해주세요.';
    } else if (lowerInput.includes('개통')) {
      return '개통은 보통 1-2 영업일 소요됩니다. 신청번호로 진행 상황을 확인하실 수 있어요.';
    } else if (lowerInput.includes('결제')) {
      return '신용카드, 체크카드, 계좌이체, 간편결제를 지원합니다. 결제 관련 문제가 있으시면 1:1 문의를 이용해주세요.';
    } else {
      return '안녕하세요! 구체적인 문의사항이 있으시면 FAQ를 먼저 확인해보시거나 1:1 문의를 이용해주세요.';
    }
  };

  const renderFAQ = () => (
    <div className="faq-section">
      <div className="faq-controls">
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="search-input"
            placeholder="FAQ 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="category-filter">
          <button
            className={`category-button ${selectedCategory === '' ? 'active' : ''}`}
            onClick={() => setSelectedCategory('')}
          >
            전체
          </button>
          {categories.map(category => (
            <button
              key={category}
              className={`category-button ${selectedCategory === category ? 'active' : ''}`}
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      <div className="faq-list">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <LoadingSpinner />
          </div>
        ) : filteredFaqs.length > 0 ? (
          filteredFaqs.map(faq => (
            <div key={faq.id} className="faq-item">
              <div
                className={`faq-question ${expandedFaq === faq.id ? 'active' : ''}`}
                onClick={() => handleFaqClick(faq.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                  <span className="question-category">{faq.category}</span>
                  <span className="question-text">{faq.question}</span>
                </div>
                <span className={`expand-icon ${expandedFaq === faq.id ? 'expanded' : ''}`}>
                  ▼
                </span>
              </div>
              {expandedFaq === faq.id && (
                <div className="faq-answer">
                  {faq.answer}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="no-results">
            <div className="no-results-icon">❓</div>
            <p>검색 결과가 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderInquiry = () => (
    <div className="inquiry-section" style={{ position: 'relative' }}>
      {inquirySubmitted && (
        <div className="success-message">
          문의가 성공적으로 접수되었습니다. 빠른 시일 내에 답변드리겠습니다.
        </div>
      )}

      <form onSubmit={handleInquirySubmit} className="inquiry-form">
        <div className="form-row">
          <div className="form-group">
            <label className="form-label required">이름</label>
            <input
              type="text"
              className="form-input"
              value={inquiryForm.name}
              onChange={(e) => setInquiryForm(prev => ({ ...prev, name: e.target.value }))}
              disabled={loading}
            />
            {formErrors.name && <div className="form-error">{formErrors.name}</div>}
          </div>
          <div className="form-group">
            <label className="form-label required">이메일</label>
            <input
              type="email"
              className="form-input"
              value={inquiryForm.email}
              onChange={(e) => setInquiryForm(prev => ({ ...prev, email: e.target.value }))}
              disabled={loading}
            />
            {formErrors.email && <div className="form-error">{formErrors.email}</div>}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">연락처</label>
            <input
              type="tel"
              className="form-input"
              placeholder="010-0000-0000"
              value={inquiryForm.phone}
              onChange={(e) => setInquiryForm(prev => ({ ...prev, phone: e.target.value }))}
              disabled={loading}
            />
          </div>
          <div className="form-group">
            <label className="form-label">신청번호</label>
            <input
              type="text"
              className="form-input"
              placeholder="MZ20240101001"
              value={inquiryForm.order_number}
              onChange={(e) => setInquiryForm(prev => ({ ...prev, order_number: e.target.value }))}
              disabled={loading}
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label required">문의 유형</label>
          <select
            className="form-select"
            value={inquiryForm.category}
            onChange={(e) => setInquiryForm(prev => ({ ...prev, category: e.target.value }))}
            disabled={loading}
          >
            <option value="">선택해주세요</option>
            {inquiryCategories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          {formErrors.category && <div className="form-error">{formErrors.category}</div>}
        </div>

        <div className="form-group">
          <label className="form-label required">제목</label>
          <input
            type="text"
            className="form-input"
            value={inquiryForm.subject}
            onChange={(e) => setInquiryForm(prev => ({ ...prev, subject: e.target.value }))}
            disabled={loading}
          />
          {formErrors.subject && <div className="form-error">{formErrors.subject}</div>}
        </div>

        <div className="form-group">
          <label className="form-label required">문의 내용</label>
          <textarea
            className="form-textarea"
            value={inquiryForm.content}
            onChange={(e) => setInquiryForm(prev => ({ ...prev, content: e.target.value }))}
            disabled={loading}
          />
          {formErrors.content && <div className="form-error">{formErrors.content}</div>}
        </div>

        <button
          type="submit"
          className="submit-button"
          disabled={loading}
        >
          {loading ? '접수 중...' : '문의 접수'}
        </button>
      </form>

      {loading && (
        <div className="loading-overlay">
          <LoadingSpinner />
        </div>
      )}
    </div>
  );

  const renderChat = () => (
    <div className="chatbot-section">
      <div className="chat-messages">
        {chatMessages.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
            <p>안녕하세요! 궁금한 것이 있으시면 언제든 물어보세요.</p>
          </div>
        ) : (
          chatMessages.map(message => (
            <div key={message.id} className={`chat-message ${message.type}`}>
              <div className="message-avatar">
                {message.type === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-content">
                {message.content}
              </div>
            </div>
          ))
        )}
      </div>
      <div className="chat-input-area">
        <input
          type="text"
          className="chat-input"
          placeholder="메시지를 입력하세요..."
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleChatSend()}
        />
        <button
          className="chat-send-button"
          onClick={handleChatSend}
          disabled={!chatInput.trim()}
        >
          전송
        </button>
      </div>
    </div>
  );

  return (
    <div className="support-page">
      <div className="support-container">
        <div className="page-header">
          <h1 className="page-title">고객 지원</h1>
          <p className="page-subtitle">궁금한 점이 있으시면 언제든 문의해주세요</p>
        </div>

        <div className="support-tabs">
          <button
            className={`tab-button ${activeTab === 'faq' ? 'active' : ''}`}
            onClick={() => setActiveTab('faq')}
          >
            자주 묻는 질문
          </button>
          <button
            className={`tab-button ${activeTab === 'inquiry' ? 'active' : ''}`}
            onClick={() => setActiveTab('inquiry')}
          >
            1:1 문의
          </button>
          <button
            className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            실시간 채팅
          </button>
        </div>

        <div className="support-content">
          {activeTab === 'faq' && renderFAQ()}
          {activeTab === 'inquiry' && renderInquiry()}
          {activeTab === 'chat' && renderChat()}
        </div>
      </div>
    </div>
  );
};

export default SupportPage;