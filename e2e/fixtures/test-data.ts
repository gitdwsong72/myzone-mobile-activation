/**
 * E2E 테스트용 테스트 데이터
 */

export const testUser = {
  name: '홍길동',
  phone: '010-1234-5678',
  email: 'hong@example.com',
  birthDate: '1990-01-01',
  gender: 'M',
  address: '서울시 강남구 테헤란로 123',
  detailAddress: '456호',
  zipCode: '12345'
};

export const testAdmin = {
  username: 'admin',
  password: 'admin123!',
  email: 'admin@myzone.com'
};

export const testPlan = {
  name: '5G 프리미엄',
  monthlyFee: 55000,
  category: '5G'
};

export const testDevice = {
  brand: 'Samsung',
  model: 'Galaxy S24',
  color: 'Black',
  price: 1200000
};

export const testNumber = {
  number: '010-1111-2222',
  category: '일반'
};

export const testPayment = {
  method: 'credit_card',
  cardNumber: '1234-5678-9012-3456',
  expiryMonth: '12',
  expiryYear: '25',
  cvc: '123',
  installment: 0
};

export const testDelivery = {
  recipientName: '홍길동',
  recipientPhone: '010-1234-5678',
  address: '서울시 강남구 테헤란로 123',
  detailAddress: '456호',
  zipCode: '12345',
  deliveryRequest: '문 앞에 놓아주세요'
};