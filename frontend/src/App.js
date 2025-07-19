import { useState, useEffect } from 'react';
import LoginRegister from './LoginRegister';
import MainInterface from './MainInterface';

function App() {
  // Lấy user từ localStorage khi load lại trang
  const [user, setUser] = useState(() => {
    const u = localStorage.getItem("daomed_user");
    return u && u !== "null" ? u : null;
  });

  // Khi user thay đổi, lưu vào localStorage
  useEffect(() => {
    if (user) {
      localStorage.setItem("daomed_user", user);
    } else {
              localStorage.removeItem("daomed_user");
    }
  }, [user]);

  // DEBUG: log user để kiểm tra
  console.log('user:', user);

  if (!user) {
    return <LoginRegister onLoginSuccess={setUser} />;
  }

  return <MainInterface user={user} onLogout={() => setUser(null)} />;
}

export default App;
