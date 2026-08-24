export const apiFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
  let token = localStorage.getItem('token');
  
  if (!options.headers) {
    options.headers = {};
  }
  
  if (token) {
    (options.headers as any)['Authorization'] = `Bearer ${token}`;
  }
  
  let response = await fetch(url, options);
  
  // Eğer 401 (Unauthorized) aldıysak ve elimizde refresh token varsa
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (refreshToken) {
      try {
        const refreshResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken })
        });
        
        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          // Yeni tokenları kaydet
          localStorage.setItem('token', data.access_token);
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token);
          }
          
          // Orijinal isteği yeni token ile tekrarla
          (options.headers as any)['Authorization'] = `Bearer ${data.access_token}`;
          response = await fetch(url, options);
        } else {
          // Refresh token da geçersizse çıkış yap
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } catch (error) {
        console.error('Refresh token error:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    } else {
      // Refresh token yoksa çıkış yap
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  }
  
  return response;
};
