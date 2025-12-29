import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Lock, Mail, LogIn, UserPlus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin
        ? { email, password }
        : { email, password, name };

      const response = await axios.post(`${API}${endpoint}`, payload);
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      toast.success(isLogin ? 'Login realizado com sucesso!' : 'Conta criada com sucesso!');
      navigate('/');
    } catch (error) {
      console.error('Auth error:', error);
      toast.error(
        error.response?.data?.detail || 
        'Erro ao processar sua solicitação'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <div 
        className="absolute inset-0 z-0"
        style={{
          backgroundImage: 'url(https://images.unsplash.com/photo-1762279389083-abf71f22d338?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzl8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGJsdWUlMjBuZW9uJTIwZmluYW5jaWFsJTIwZGF0YSUyMHZpc3VhbGl6YXRpb24lMjBiYWNrZ3JvdW5kfGVufDB8fHx8MTc2NzA0MzU1OHww&ixlib=rb-4.1.0&q=85)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/95 via-slate-900/90 to-blue-900/80" />
      </div>

      <div className="relative z-10 w-full max-w-md px-6">
        <div className="glass-card rounded-2xl p-8 md:p-12 space-y-8">
          <div className="text-center space-y-3">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 glow-blue mb-4">
              <Lock className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              FinFamily
            </h1>
            <p className="text-slate-400 text-lg">
              {isLogin ? 'Entre na sua conta' : 'Crie sua conta'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="name" className="text-slate-300">
                  Nome Completo
                </Label>
                <Input
                  id="name"
                  data-testid="register-name-input"
                  type="text"
                  placeholder="Seu nome"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="bg-slate-950 border-slate-800 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 h-12 px-4"
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-300">
                Email
              </Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <Input
                  id="email"
                  data-testid="login-email-input"
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-slate-950 border-slate-800 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 h-12 pl-11 pr-4"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-300">
                Senha
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <Input
                  id="password"
                  data-testid="login-password-input"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="bg-slate-950 border-slate-800 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 h-12 pl-11 pr-4"
                />
              </div>
            </div>

            <Button
              type="submit"
              data-testid={isLogin ? 'login-submit-button' : 'register-submit-button'}
              disabled={loading}
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl glow-blue button-glow"
            >
              {loading ? (
                'Processando...'
              ) : isLogin ? (
                <>
                  <LogIn className="w-5 h-5 mr-2" />
                  Entrar
                </>
              ) : (
                <>
                  <UserPlus className="w-5 h-5 mr-2" />
                  Criar Conta
                </>
              )}
            </Button>
          </form>

          <div className="text-center pt-4 border-t border-slate-800">
            <button
              type="button"
              data-testid="toggle-auth-mode-button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
            >
              {isLogin
                ? 'Não tem uma conta? Cadastre-se'
                : 'Já tem uma conta? Faça login'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}