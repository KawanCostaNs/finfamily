import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  User,
  Mail,
  Lock,
  Camera,
  Save,
  Trash2,
  AlertTriangle,
  Eye,
  EyeOff,
  Calendar,
  Shield,
  Bell,
  Palette,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Profile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [profilePhoto, setProfilePhoto] = useState('');
  
  // Password change states
  const [passwordDialog, setPasswordDialog] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  
  // Delete confirmation states
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deleting, setDeleting] = useState(false);
  
  // Preferences
  const [preferences, setPreferences] = useState({
    emailNotifications: true,
    darkMode: true,
    currency: 'BRL',
    language: 'pt-BR',
  });

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      const userData = response.data;
      setUser(userData);
      setName(userData.name || '');
      setEmail(userData.email || '');
      setProfilePhoto(userData.profile_photo || '');
      
      if (userData.preferences) {
        setPreferences(prev => ({ ...prev, ...userData.preferences }));
      }
    } catch (error) {
      console.error('Error fetching user data:', error);
      // Fallback to localStorage data
      const localUser = JSON.parse(localStorage.getItem('user') || '{}');
      setUser(localUser);
      setName(localUser.name || '');
      setEmail(localUser.email || '');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const response = await axios.put(
        `${API}/profile`,
        {
          name,
          profile_photo: profilePhoto,
          preferences,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Update localStorage
      const updatedUser = { ...user, name, profile_photo: profilePhoto };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      
      toast.success('Perfil atualizado com sucesso!');
    } catch (error) {
      console.error('Error saving profile:', error);
      toast.error('Erro ao salvar perfil');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error('As senhas não coincidem');
      return;
    }
    
    if (newPassword.length < 6) {
      toast.error('A nova senha deve ter pelo menos 6 caracteres');
      return;
    }

    try {
      await axios.post(
        `${API}/profile/change-password`,
        {
          current_password: currentPassword,
          new_password: newPassword,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Senha alterada com sucesso!');
      setPasswordDialog(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      console.error('Error changing password:', error);
      const message = error.response?.data?.detail || 'Erro ao alterar senha';
      toast.error(message);
    }
  };

  const handleDeleteAllTransactions = async () => {
    if (deleteConfirmText !== 'EXCLUIR TUDO') {
      toast.error('Digite "EXCLUIR TUDO" para confirmar');
      return;
    }

    setDeleting(true);
    try {
      const response = await axios.delete(`${API}/transactions/delete-all`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      toast.success(response.data.message || 'Todas as transações foram excluídas!');
      setDeleteDialog(false);
      setDeleteConfirmText('');
    } catch (error) {
      console.error('Error deleting transactions:', error);
      toast.error('Erro ao excluir transações');
    } finally {
      setDeleting(false);
    }
  };

  const handlePhotoUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      // Convert to base64 for simple storage
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfilePhoto(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const getInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Carregando perfil...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1
          className="text-4xl md:text-5xl font-bold text-white mb-2"
          style={{ fontFamily: 'Manrope, sans-serif' }}
        >
          Meu Perfil
        </h1>
        <p className="text-slate-400 text-lg">Gerencie suas informações pessoais e preferências</p>
      </div>

      {/* Profile Photo & Basic Info */}
      <Card className="glass-card border-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <User className="w-5 h-5 text-blue-400" />
            Informações Pessoais
          </CardTitle>
          <CardDescription className="text-slate-400">
            Atualize sua foto e dados básicos
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Photo Section */}
          <div className="flex items-center gap-6">
            <div className="relative">
              {profilePhoto ? (
                <img
                  src={profilePhoto}
                  alt="Foto de perfil"
                  className="w-24 h-24 rounded-full object-cover border-4 border-blue-500/50"
                />
              ) : (
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold border-4 border-blue-500/50">
                  {getInitials(name)}
                </div>
              )}
              <label
                htmlFor="photo-upload"
                className="absolute bottom-0 right-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center cursor-pointer hover:bg-blue-700 transition-colors"
              >
                <Camera className="w-4 h-4 text-white" />
                <input
                  id="photo-upload"
                  type="file"
                  accept="image/*"
                  onChange={handlePhotoUpload}
                  className="hidden"
                />
              </label>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-white">{name || 'Usuário'}</h3>
              <p className="text-slate-400">{email}</p>
              {user?.is_admin && (
                <span className="inline-flex items-center gap-1 px-2 py-1 mt-2 bg-amber-500/20 text-amber-400 text-xs rounded-full">
                  <Shield className="w-3 h-3" />
                  Administrador
                </span>
              )}
            </div>
          </div>

          {/* Form Fields */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label className="text-slate-300">Nome Completo</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Seu nome"
                  className="bg-slate-950 border-slate-800 text-white pl-10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <Input
                  value={email}
                  disabled
                  className="bg-slate-950 border-slate-800 text-slate-500 pl-10 cursor-not-allowed"
                />
              </div>
              <p className="text-xs text-slate-500">O email não pode ser alterado</p>
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              onClick={handleSaveProfile}
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Salvando...' : 'Salvar Alterações'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card className="glass-card border-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Lock className="w-5 h-5 text-green-400" />
            Segurança
          </CardTitle>
          <CardDescription className="text-slate-400">
            Gerencie sua senha e configurações de segurança
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
            <div>
              <h4 className="text-white font-medium">Alterar Senha</h4>
              <p className="text-sm text-slate-400">Atualize sua senha periodicamente para maior segurança</p>
            </div>
            <Button
              onClick={() => setPasswordDialog(true)}
              variant="outline"
              className="border-slate-700 text-white hover:bg-slate-800"
            >
              <Lock className="w-4 h-4 mr-2" />
              Alterar
            </Button>
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
            <div>
              <h4 className="text-white font-medium">Conta criada em</h4>
              <p className="text-sm text-slate-400">
                {user?.created_at 
                  ? new Date(user.created_at).toLocaleDateString('pt-BR', {
                      day: '2-digit',
                      month: 'long',
                      year: 'numeric'
                    })
                  : 'Data não disponível'}
              </p>
            </div>
            <Calendar className="w-5 h-5 text-slate-500" />
          </div>
        </CardContent>
      </Card>

      {/* Preferences */}
      <Card className="glass-card border-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Palette className="w-5 h-5 text-purple-400" />
            Preferências
          </CardTitle>
          <CardDescription className="text-slate-400">
            Personalize sua experiência no aplicativo
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-blue-400" />
              <div>
                <h4 className="text-white font-medium">Notificações por Email</h4>
                <p className="text-sm text-slate-400">Receba alertas sobre suas finanças</p>
              </div>
            </div>
            <Switch
              checked={preferences.emailNotifications}
              onCheckedChange={(checked) => 
                setPreferences(prev => ({ ...prev, emailNotifications: checked }))
              }
            />
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
            <div className="flex items-center gap-3">
              <Palette className="w-5 h-5 text-purple-400" />
              <div>
                <h4 className="text-white font-medium">Tema Escuro</h4>
                <p className="text-sm text-slate-400">Usar tema escuro no aplicativo</p>
              </div>
            </div>
            <Switch
              checked={preferences.darkMode}
              onCheckedChange={(checked) => 
                setPreferences(prev => ({ ...prev, darkMode: checked }))
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="glass-card border-red-500/30 bg-red-950/10">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-400">
            <AlertTriangle className="w-5 h-5" />
            Zona de Perigo
          </CardTitle>
          <CardDescription className="text-red-300/70">
            Ações irreversíveis - tenha cuidado!
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 bg-red-900/20 rounded-lg border border-red-500/30">
            <div>
              <h4 className="text-red-400 font-medium">Excluir Todas as Transações</h4>
              <p className="text-sm text-red-300/70">
                Esta ação não pode ser desfeita. Todas as suas transações serão permanentemente removidas.
              </p>
            </div>
            <Button
              onClick={() => setDeleteDialog(true)}
              variant="destructive"
              className="bg-red-600 hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Excluir Tudo
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Change Password Dialog */}
      <Dialog open={passwordDialog} onOpenChange={setPasswordDialog}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle>Alterar Senha</DialogTitle>
            <DialogDescription className="text-slate-400">
              Digite sua senha atual e escolha uma nova senha
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Senha Atual</Label>
              <div className="relative">
                <Input
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Digite sua senha atual"
                  className="bg-slate-950 border-slate-800 text-white pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
                >
                  {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Nova Senha</Label>
              <div className="relative">
                <Input
                  type={showNewPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Digite a nova senha"
                  className="bg-slate-950 border-slate-800 text-white pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
                >
                  {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Confirmar Nova Senha</Label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirme a nova senha"
                className="bg-slate-950 border-slate-800 text-white"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setPasswordDialog(false);
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
              }}
              className="text-slate-400"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleChangePassword}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Alterar Senha
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete All Transactions Confirmation */}
      <AlertDialog open={deleteDialog} onOpenChange={setDeleteDialog}>
        <AlertDialogContent className="bg-slate-900 border-red-500/30">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-red-400 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Confirmar Exclusão
            </AlertDialogTitle>
            <AlertDialogDescription className="text-slate-400">
              <p className="mb-4">
                <strong className="text-red-400">ATENÇÃO:</strong> Esta ação é IRREVERSÍVEL!
              </p>
              <p className="mb-4">
                Todas as suas transações serão permanentemente excluídas do sistema. 
                Isso inclui transações importadas, categorizadas e marcadas como reserva de emergência.
              </p>
              <p className="mb-4 text-white">
                Para confirmar, digite <strong className="text-red-400">EXCLUIR TUDO</strong> no campo abaixo:
              </p>
              <Input
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="Digite EXCLUIR TUDO"
                className="bg-slate-950 border-red-500/50 text-white"
              />
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel 
              className="bg-slate-800 text-white border-slate-700 hover:bg-slate-700"
              onClick={() => setDeleteConfirmText('')}
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteAllTransactions}
              disabled={deleteConfirmText !== 'EXCLUIR TUDO' || deleting}
              className="bg-red-600 hover:bg-red-700 disabled:opacity-50"
            >
              {deleting ? 'Excluindo...' : 'Excluir Permanentemente'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
