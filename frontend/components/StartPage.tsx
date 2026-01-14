import React from 'react';
import { useNavigate } from 'react-router-dom';

const StartPage = () => {
  const navigate = useNavigate();
  return (
    <div style={{ padding: '50px', textAlign: 'center', color: 'white' }}>
      <h1>Senior1 AI 硬體分析系統</h1>
      <p>歡迎使用！請點擊下方按鈕開始。</p>
      <button 
        onClick={() => navigate('/benchmark')}
        style={{ padding: '12px 24px', backgroundColor: '#76b900', border: 'none', color: 'white', cursor: 'pointer', borderRadius: '5px', fontSize: '1.1rem' }}
      >
        進入基準測試
      </button>
    </div>
  );
};

export default StartPage;