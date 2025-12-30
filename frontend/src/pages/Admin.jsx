import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Users, CheckCircle, XCircle, Shield, UserCheck, UserX, Key } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Admin() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);
  const [resetPasswordDialog, setResetPasswordDialog] = useState({ open: false, email: null });
  const [newPassword, setNewPassword] = useState('');

  const token = localStorage.getItem('token');

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUser(user);
      if (!user.is_admin) {
        toast.error('Acesso negado: apenas administradores');
        return;
      }
    }
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Erro ao carregar usuários');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (email) => {
    try {
      await axios.post(
        `${API}/admin/users/${email}/approve`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Usuário aprovado com sucesso!');
      fetchUsers();
    } catch (error) {
      console.error('Error approving user:', error);
      toast.error('Erro ao aprovar usuário');
    }
  };

  const handleDelete = async (email) => {
    if (!window.confirm(`Tem certeza que deseja excluir o usuário ${email}?`)) return;

    try {
      await axios.delete(`${API}/admin/users/${email}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Usuário excluído com sucesso');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('Erro ao excluir usuário');
    }
  };

  const handleResetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error('Senha deve ter no mínimo 6 caracteres');
      return;
    }

    try {
      await axios.post(
        `${API}/admin/users/${resetPasswordDialog.email}/reset-password`,
        { new_password: newPassword },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Senha resetada com sucesso!');
      setResetPasswordDialog({ open: false, email: null });
      setNewPassword('');
    } catch (error) {
      console.error('Error resetting password:', error);
      toast.error('Erro ao resetar senha');
    }
  };

  if (!currentUser?.is_admin) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="glass-card border-slate-800 max-w-md">
          <CardContent className="pt-6 text-center">
            <Shield className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Acesso Negado</h2>
            <p className="text-slate-400">Apenas administradores podem acessar esta página</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Carregando usuários...</p>
        </div>
      </div>
    );
  }

  const pendingUsers = users.filter((u) => !u.is_approved);
  const approvedUsers = users.filter((u) => u.is_approved);

  return (
    <div className="space-y-8">
      <div>
        <h1
          className="text-4xl md:text-5xl font-bold text-white mb-2"
          style={{ fontFamily: 'Manrope, sans-serif' }}
        >
          Administração
        </h1>
        <p className="text-slate-400 text-lg">Gerencie usuários e permissões do sistema</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="glass-card border-slate-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">Total de Usuários</p>
                <p className="text-3xl font-bold text-white font-mono">{users.length}</p>
              </div>
              <Users className="w-12 h-12 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-slate-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">Pendentes</p>
                <p className="text-3xl font-bold text-amber-400 font-mono">{pendingUsers.length}</p>
              </div>
              <UserCheck className="w-12 h-12 text-amber-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card border-slate-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">Aprovados</p>
                <p className="text-3xl font-bold text-green-400 font-mono">{approvedUsers.length}</p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Users */}
      {pendingUsers.length > 0 && (
        <Card className="solid-card border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-amber-400" />
              Usuários Pendentes de Aprovação
            </CardTitle>
            <CardDescription className="text-slate-400">
              Novos usuários aguardando aprovação do administrador
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pendingUsers.map((user) => (
                <div
                  key={user.id}
                  data-testid="pending-user-card"
                  className="glass-card p-4 rounded-xl border-slate-800 hover:border-amber-500/30 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{user.name}</h3>
                      <p className="text-sm text-slate-400">{user.email}</p>
                      <span className="inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-400">
                        Aguardando Aprovação
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        data-testid="approve-user-button"
                        onClick={() => handleApprove(user.email)}
                        className="bg-green-600 hover:bg-green-700 glow-green"
                      >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Aprovar
                      </Button>
                      <Button
                        data-testid="delete-user-button"
                        onClick={() => handleDelete(user.email)}
                        variant="ghost"
                        className="text-red-400 hover:text-red-300 hover:bg-slate-800"
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        Rejeitar
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Approved Users */}
      <Card className="solid-card border-slate-800">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-400" />
            Usuários Aprovados ({approvedUsers.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {approvedUsers.map((user) => (
              <div
                key={user.id}
                data-testid="approved-user-card"
                className="glass-card p-4 rounded-xl border-slate-800"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-white">{user.name}</h3>
                      {user.is_admin && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400">
                          <Shield className="w-3 h-3" />
                          Admin
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-400 mt-1">{user.email}</p>
                    <span className="inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400">
                      Ativo
                    </span>
                  </div>
                  {!user.is_admin && (
                    <Button
                      onClick={() => handleDelete(user.email)}
                      variant="ghost"
                      className="text-red-400 hover:text-red-300 hover:bg-slate-800"
                    >
                      <UserX className="w-4 h-4 mr-2" />
                      Remover
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
