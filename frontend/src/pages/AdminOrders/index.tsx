import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../../store/store';
import Button from '../../components/Common/Button';
import Modal from '../../components/Common/Modal';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import { useToast } from '../../components/Common/Toast';
import './AdminOrders.css';

interface Order {
  id: number;
  order_number: string;
  user_name: string;
  user_phone: string;
  plan_name: string;
  device_model: string;
  number: string;
  status: 'pending' | 'processing' | 'completed' | 'cancelled';
  total_amount: number;
  created_at: string;
  updated_at: string;
}

interface OrderDetail extends Order {
  user_email: string;
  user_address: string;
  delivery_address: string;
  payment_method: string;
  payment_status: string;
  notes: string;
  status_history: Array<{
    status: string;
    note: string;
    admin_name: string;
    created_at: string;
  }>;
}

const AdminOrders: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { showSuccess, showError } = useToast();
  
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<OrderDetail | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [statusNote, setStatusNote] = useState('');
  
  // 필터 상태
  const [filters, setFilters] = useState({
    status: '',
    dateFrom: '',
    dateTo: '',
    search: ''
  });
  
  // 페이지네이션 상태
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [itemsPerPage] = useState(20);

  useEffect(() => {
    fetchOrders();
  }, [currentPage, filters]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      // API 호출 시뮬레이션
      const mockOrders: Order[] = [
        {
          id: 1,
          order_number: 'ORD-2024-001',
          user_name: '홍길동',
          user_phone: '010-1234-5678',
          plan_name: '5G 프리미엄',
          device_model: 'iPhone 15 Pro',
          number: '010-9999-1234',
          status: 'pending',
          total_amount: 1200000,
          created_at: '2024-01-15T10:30:00Z',
          updated_at: '2024-01-15T10:30:00Z'
        },
        {
          id: 2,
          order_number: 'ORD-2024-002',
          user_name: '김영희',
          user_phone: '010-2345-6789',
          plan_name: 'LTE 베이직',
          device_model: 'Galaxy S24',
          number: '010-8888-5678',
          status: 'processing',
          total_amount: 800000,
          created_at: '2024-01-15T11:15:00Z',
          updated_at: '2024-01-15T14:20:00Z'
        },
        {
          id: 3,
          order_number: 'ORD-2024-003',
          user_name: '박민수',
          user_phone: '010-3456-7890',
          plan_name: '5G 스탠다드',
          device_model: 'iPhone 15',
          number: '010-7777-9012',
          status: 'completed',
          total_amount: 950000,
          created_at: '2024-01-14T16:45:00Z',
          updated_at: '2024-01-15T09:30:00Z'
        }
      ];
      
      setOrders(mockOrders);
      setTotalPages(Math.ceil(mockOrders.length / itemsPerPage));
    } catch (error) {
      showError('주문 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderDetail = async (orderId: number) => {
    try {
      // API 호출 시뮬레이션
      const mockOrderDetail: OrderDetail = {
        id: orderId,
        order_number: 'ORD-2024-001',
        user_name: '홍길동',
        user_phone: '010-1234-5678',
        user_email: 'hong@example.com',
        user_address: '서울시 강남구 테헤란로 123',
        plan_name: '5G 프리미엄',
        device_model: 'iPhone 15 Pro',
        number: '010-9999-1234',
        status: 'pending',
        total_amount: 1200000,
        delivery_address: '서울시 강남구 테헤란로 123',
        payment_method: '신용카드',
        payment_status: '결제완료',
        notes: '',
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-15T10:30:00Z',
        status_history: [
          {
            status: 'pending',
            note: '주문이 접수되었습니다.',
            admin_name: '시스템',
            created_at: '2024-01-15T10:30:00Z'
          }
        ]
      };
      
      setSelectedOrder(mockOrderDetail);
    } catch (error) {
      showError('주문 상세 정보를 불러오는데 실패했습니다.');
    }
  };

  const handleOrderClick = async (order: Order) => {
    await fetchOrderDetail(order.id);
    setShowDetailModal(true);
  };

  const handleStatusChange = (order: Order) => {
    setSelectedOrder(order as OrderDetail);
    setNewStatus(order.status);
    setStatusNote('');
    setShowStatusModal(true);
  };

  const submitStatusChange = async () => {
    if (!selectedOrder || !newStatus) return;
    
    try {
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 주문 목록 업데이트
      setOrders(prev => prev.map(order => 
        order.id === selectedOrder.id 
          ? { ...order, status: newStatus as any, updated_at: new Date().toISOString() }
          : order
      ));
      
      setShowStatusModal(false);
      showSuccess('주문 상태가 성공적으로 변경되었습니다.');
    } catch (error) {
      showError('주문 상태 변경에 실패했습니다.');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { label: '접수대기', className: 'status-pending' },
      processing: { label: '처리중', className: 'status-processing' },
      completed: { label: '완료', className: 'status-completed' },
      cancelled: { label: '취소', className: 'status-cancelled' }
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    return <span className={`status-badge ${config.className}`}>{config.label}</span>;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW'
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const resetFilters = () => {
    setFilters({
      status: '',
      dateFrom: '',
      dateTo: '',
      search: ''
    });
    setCurrentPage(1);
  };

  return (
    <div className="admin-orders">
      <div className="admin-orders__header">
        <h1>주문 관리</h1>
        <p>고객의 개통 신청을 관리하고 처리하세요</p>
      </div>

      {/* 필터 섹션 */}
      <div className="admin-orders__filters">
        <div className="filters-row">
          <div className="filter-group">
            <label>상태</label>
            <select 
              value={filters.status} 
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">전체</option>
              <option value="pending">접수대기</option>
              <option value="processing">처리중</option>
              <option value="completed">완료</option>
              <option value="cancelled">취소</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>시작일</label>
            <input 
              type="date" 
              value={filters.dateFrom}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
            />
          </div>
          
          <div className="filter-group">
            <label>종료일</label>
            <input 
              type="date" 
              value={filters.dateTo}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
            />
          </div>
          
          <div className="filter-group">
            <label>검색</label>
            <input 
              type="text" 
              placeholder="주문번호, 고객명, 전화번호"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>
          
          <div className="filter-actions">
            <Button variant="outline" onClick={resetFilters}>
              초기화
            </Button>
          </div>
        </div>
      </div>

      {/* 주문 테이블 */}
      <div className="admin-orders__content">
        {loading ? (
          <div className="loading-container">
            <LoadingSpinner size="large" />
            <p>주문 목록을 불러오는 중...</p>
          </div>
        ) : (
          <>
            <div className="orders-table-container">
              <table className="orders-table">
                <thead>
                  <tr>
                    <th>주문번호</th>
                    <th>고객정보</th>
                    <th>상품정보</th>
                    <th>금액</th>
                    <th>상태</th>
                    <th>신청일시</th>
                    <th>작업</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id} className="order-row">
                      <td>
                        <button 
                          className="order-number-link"
                          onClick={() => handleOrderClick(order)}
                        >
                          {order.order_number}
                        </button>
                      </td>
                      <td>
                        <div className="customer-info">
                          <div className="customer-name">{order.user_name}</div>
                          <div className="customer-phone">{order.user_phone}</div>
                        </div>
                      </td>
                      <td>
                        <div className="product-info">
                          <div className="plan-name">{order.plan_name}</div>
                          <div className="device-model">{order.device_model}</div>
                          <div className="phone-number">{order.number}</div>
                        </div>
                      </td>
                      <td className="amount">{formatCurrency(order.total_amount)}</td>
                      <td>{getStatusBadge(order.status)}</td>
                      <td className="date">{formatDate(order.created_at)}</td>
                      <td>
                        <div className="action-buttons">
                          <Button 
                            size="small" 
                            variant="outline"
                            onClick={() => handleOrderClick(order)}
                          >
                            상세
                          </Button>
                          <Button 
                            size="small" 
                            variant="primary"
                            onClick={() => handleStatusChange(order)}
                          >
                            상태변경
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 페이지네이션 */}
            <div className="pagination">
              <Button 
                variant="outline" 
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(prev => prev - 1)}
              >
                이전
              </Button>
              <span className="page-info">
                {currentPage} / {totalPages}
              </span>
              <Button 
                variant="outline" 
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(prev => prev + 1)}
              >
                다음
              </Button>
            </div>
          </>
        )}
      </div>

      {/* 주문 상세 모달 */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title="주문 상세 정보"
        size="large"
      >
        {selectedOrder && (
          <div className="order-detail">
            <div className="order-detail__tabs">
              <div className="tab-content">
                <div className="detail-section">
                  <h3>기본 정보</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>주문번호</label>
                      <span>{selectedOrder.order_number}</span>
                    </div>
                    <div className="detail-item">
                      <label>상태</label>
                      {getStatusBadge(selectedOrder.status)}
                    </div>
                    <div className="detail-item">
                      <label>신청일시</label>
                      <span>{formatDate(selectedOrder.created_at)}</span>
                    </div>
                    <div className="detail-item">
                      <label>최종수정</label>
                      <span>{formatDate(selectedOrder.updated_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3>고객 정보</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>이름</label>
                      <span>{selectedOrder.user_name}</span>
                    </div>
                    <div className="detail-item">
                      <label>전화번호</label>
                      <span>{selectedOrder.user_phone}</span>
                    </div>
                    <div className="detail-item">
                      <label>이메일</label>
                      <span>{selectedOrder.user_email}</span>
                    </div>
                    <div className="detail-item">
                      <label>주소</label>
                      <span>{selectedOrder.user_address}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3>상품 정보</h3>
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>요금제</label>
                      <span>{selectedOrder.plan_name}</span>
                    </div>
                    <div className="detail-item">
                      <label>단말기</label>
                      <span>{selectedOrder.device_model}</span>
                    </div>
                    <div className="detail-item">
                      <label>전화번호</label>
                      <span>{selectedOrder.number}</span>
                    </div>
                    <div className="detail-item">
                      <label>총 금액</label>
                      <span className="amount">{formatCurrency(selectedOrder.total_amount)}</span>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3>처리 이력</h3>
                  <div className="status-history">
                    {selectedOrder.status_history.map((history, index) => (
                      <div key={index} className="history-item">
                        <div className="history-status">{getStatusBadge(history.status)}</div>
                        <div className="history-content">
                          <div className="history-note">{history.note}</div>
                          <div className="history-meta">
                            {history.admin_name} • {formatDate(history.created_at)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* 상태 변경 모달 */}
      <Modal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        title="주문 상태 변경"
      >
        <div className="status-change-form">
          <div className="form-group">
            <label>새로운 상태</label>
            <select 
              value={newStatus} 
              onChange={(e) => setNewStatus(e.target.value)}
            >
              <option value="pending">접수대기</option>
              <option value="processing">처리중</option>
              <option value="completed">완료</option>
              <option value="cancelled">취소</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>처리 메모</label>
            <textarea 
              value={statusNote}
              onChange={(e) => setStatusNote(e.target.value)}
              placeholder="상태 변경 사유나 메모를 입력하세요"
              rows={3}
            />
          </div>
          
          <div className="modal-actions">
            <Button variant="outline" onClick={() => setShowStatusModal(false)}>
              취소
            </Button>
            <Button variant="primary" onClick={submitStatusChange}>
              변경
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default AdminOrders;