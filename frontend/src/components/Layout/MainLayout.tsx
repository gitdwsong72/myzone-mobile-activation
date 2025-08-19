import React from 'react';
import Header from './Header';
import Footer from './Footer';
import Sidebar from './Sidebar';
import { useAppSelector } from '../../store/hooks';

interface MainLayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
  isAdmin?: boolean;
}

const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  showSidebar = false,
  isAdmin = false,
}) => {
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  return (
    <div className={`main-layout ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <Header />
      
      <div className="layout-content">
        {showSidebar && <Sidebar isAdmin={isAdmin} />}
        
        <main className={`main-content ${showSidebar ? 'with-sidebar' : ''}`}>
          {children}
        </main>
      </div>
      
      <Footer />
    </div>
  );
};

export default MainLayout;