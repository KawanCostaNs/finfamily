import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Users, Building2, Tag, Plus, Pencil, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Settings() {
  const [activeTab, setActiveTab] = useState('family');
  const [members, setMembers] = useState([]);
  const [banks, setBanks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  const [memberDialog, setMemberDialog] = useState({ open: false, data: null });
  const [bankDialog, setBankDialog] = useState({ open: false, data: null });
  const [categoryDialog, setCategoryDialog] = useState({ open: false, data: null });

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [membersRes, banksRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/family`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/banks`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/categories`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      setMembers(membersRes.data);
      setBanks(banksRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erro ao carregar configurações');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveMember = async (data) => {
    try {
      if (memberDialog.data) {
        await axios.put(`${API}/family/${memberDialog.data.id}`, data, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success('Membro atualizado com sucesso');
      } else {
        await axios.post(`${API}/family`, data, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success('Membro adicionado com sucesso');
      }
      fetchData();
      setMemberDialog({ open: false, data: null });
    } catch (error) {
      console.error('Error saving member:', error);
      toast.error('Erro ao salvar membro');
    }
  };

  const handleDeleteMember = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este membro?')) return;

    try {
      await axios.delete(`${API}/family/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Membro excluído com sucesso');
      fetchData();
    } catch (error) {
      console.error('Error deleting member:', error);
      toast.error('Erro ao excluir membro');
    }
  };

  const handleSaveBank = async (data) => {
    try {
      if (bankDialog.data) {
        await axios.put(`${API}/banks/${bankDialog.data.id}`, data, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success('Banco atualizado com sucesso');
      } else {
        await axios.post(`${API}/banks`, data, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success('Banco adicionado com sucesso');
      }
      fetchData();
      setBankDialog({ open: false, data: null });
    } catch (error) {
      console.error('Error saving bank:', error);
      toast.error('Erro ao salvar banco');
    }
  };

  const handleDeleteBank = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este banco?')) return;

    try {
      await axios.delete(`${API}/banks/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Banco excluído com sucesso');
      fetchData();
    } catch (error) {
      console.error('Error deleting bank:', error);
      toast.error('Erro ao excluir banco');
    }
  };

  const handleSaveCategory = async (data) => {
    try {
      if (categoryDialog.data) {
        await axios.put(`${API}/categories/${categoryDialog.data.id}`, data, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success('Categoria atualizada com sucesso');
      } else {
        await axios.post(`${API}/categories`, data, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success('Categoria adicionada com sucesso');
      }
      fetchData();
      setCategoryDialog({ open: false, data: null });
    } catch (error) {
      console.error('Error saving category:', error);
      toast.error('Erro ao salvar categoria');
    }
  };

  const handleDeleteCategory = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta categoria?')) return;

    try {
      await axios.delete(`${API}/categories/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Categoria excluída com sucesso');
      fetchData();
    } catch (error) {
      console.error('Error deleting category:', error);
      toast.error('Erro ao excluir categoria');
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1
          className="text-4xl md:text-5xl font-bold text-white mb-2"
          style={{ fontFamily: 'Manrope, sans-serif' }}
        >
          Configurações
        </h1>
        <p className="text-slate-400 text-lg">
          Gerencie membros da família, bancos e categorias
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-slate-900 border border-slate-800">
          <TabsTrigger
            data-testid="family-tab"
            value="family"
            className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
          >
            <Users className="w-4 h-4 mr-2" />
            Família
          </TabsTrigger>
          <TabsTrigger
            data-testid="banks-tab"
            value="banks"
            className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
          >
            <Building2 className="w-4 h-4 mr-2" />
            Bancos
          </TabsTrigger>
          <TabsTrigger
            data-testid="categories-tab"
            value="categories"
            className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
          >
            <Tag className="w-4 h-4 mr-2" />
            Categorias
          </TabsTrigger>
        </TabsList>

        {/* Family Tab */}
        <TabsContent value="family" className="space-y-4">
          <div className="flex justify-end">
            <Button
              data-testid="add-member-button"
              onClick={() => setMemberDialog({ open: true, data: null })}
              className="bg-blue-600 hover:bg-blue-700 glow-blue button-glow"
            >
              <Plus className="w-4 h-4 mr-2" />
              Adicionar Membro
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {members.map((member) => (
              <Card key={member.id} data-testid="member-card" className="glass-card border-slate-800 card-hover">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-white">{member.name}</h3>
                      {member.profile && (
                        <p className="text-sm text-slate-400 mt-1">{member.profile}</p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        data-testid="edit-member-button"
                        size="sm"
                        variant="ghost"
                        onClick={() => setMemberDialog({ open: true, data: member })}
                        className="text-blue-400 hover:text-blue-300 hover:bg-slate-800"
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        data-testid="delete-member-button"
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteMember(member.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-slate-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {members.length === 0 && (
            <Card className="solid-card border-slate-800">
              <CardContent className="py-12 text-center text-slate-500">
                Nenhum membro cadastrado. Clique em "Adicionar Membro" para começar.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Banks Tab */}
        <TabsContent value="banks" className="space-y-4">
          <div className="flex justify-end">
            <Button
              data-testid="add-bank-button"
              onClick={() => setBankDialog({ open: true, data: null })}
              className="bg-blue-600 hover:bg-blue-700 glow-blue button-glow"
            >
              <Plus className="w-4 h-4 mr-2" />
              Adicionar Banco
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {banks.map((bank) => (
              <Card key={bank.id} data-testid="bank-card" className="glass-card border-slate-800 card-hover">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-white">{bank.name}</h3>
                      <p className={`text-sm mt-1 ${bank.active ? 'text-green-400' : 'text-red-400'}`}>
                        {bank.active ? 'Ativo' : 'Inativo'}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        data-testid="edit-bank-button"
                        size="sm"
                        variant="ghost"
                        onClick={() => setBankDialog({ open: true, data: bank })}
                        className="text-blue-400 hover:text-blue-300 hover:bg-slate-800"
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        data-testid="delete-bank-button"
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteBank(bank.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-slate-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {banks.length === 0 && (
            <Card className="solid-card border-slate-800">
              <CardContent className="py-12 text-center text-slate-500">
                Nenhum banco cadastrado. Clique em "Adicionar Banco" para começar.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Categories Tab */}
        <TabsContent value="categories" className="space-y-4">
          <div className="flex justify-end">
            <Button
              data-testid="add-category-button"
              onClick={() => setCategoryDialog({ open: true, data: null })}
              className="bg-blue-600 hover:bg-blue-700 glow-blue button-glow"
            >
              <Plus className="w-4 h-4 mr-2" />
              Adicionar Categoria
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {categories.map((category) => (
              <Card key={category.id} data-testid="category-card" className="glass-card border-slate-800 card-hover">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-white">{category.name}</h3>
                      <p className="text-sm text-slate-400 mt-1 capitalize">{category.type}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        data-testid="edit-category-button"
                        size="sm"
                        variant="ghost"
                        onClick={() => setCategoryDialog({ open: true, data: category })}
                        className="text-blue-400 hover:text-blue-300 hover:bg-slate-800"
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        data-testid="delete-category-button"
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteCategory(category.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-slate-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {categories.length === 0 && (
            <Card className="solid-card border-slate-800">
              <CardContent className="py-12 text-center text-slate-500">
                Nenhuma categoria cadastrada. Clique em "Adicionar Categoria" para começar.
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Member Dialog */}
      <MemberDialog
        open={memberDialog.open}
        data={memberDialog.data}
        onClose={() => setMemberDialog({ open: false, data: null })}
        onSave={handleSaveMember}
      />

      {/* Bank Dialog */}
      <BankDialog
        open={bankDialog.open}
        data={bankDialog.data}
        onClose={() => setBankDialog({ open: false, data: null })}
        onSave={handleSaveBank}
      />

      {/* Category Dialog */}
      <CategoryDialog
        open={categoryDialog.open}
        data={categoryDialog.data}
        onClose={() => setCategoryDialog({ open: false, data: null })}
        onSave={handleSaveCategory}
      />
    </div>
  );
}

function MemberDialog({ open, data, onClose, onSave }) {
  const [name, setName] = useState('');
  const [profile, setProfile] = useState('');

  useEffect(() => {
    if (data) {
      setName(data.name);
      setProfile(data.profile || '');
    } else {
      setName('');
      setProfile('');
    }
  }, [data, open]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({ name, profile: profile || null });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-slate-900 border-slate-800 text-white">
        <DialogHeader>
          <DialogTitle>{data ? 'Editar Membro' : 'Adicionar Membro'}</DialogTitle>
          <DialogDescription className="text-slate-400">
            Preencha os dados do membro da família
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="member-name">Nome</Label>
            <Input
              id="member-name"
              data-testid="member-name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="bg-slate-950 border-slate-800 text-white"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="member-profile">Perfil (opcional)</Label>
            <Input
              id="member-profile"
              data-testid="member-profile-input"
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
              placeholder="Ex: Pai, Mãe, Filho"
              className="bg-slate-950 border-slate-800 text-white"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="text-slate-400">
              Cancelar
            </Button>
            <Button data-testid="save-member-button" type="submit" className="bg-blue-600 hover:bg-blue-700">
              Salvar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function BankDialog({ open, data, onClose, onSave }) {
  const [name, setName] = useState('');
  const [active, setActive] = useState(true);

  useEffect(() => {
    if (data) {
      setName(data.name);
      setActive(data.active);
    } else {
      setName('');
      setActive(true);
    }
  }, [data, open]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({ name, active });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-slate-900 border-slate-800 text-white">
        <DialogHeader>
          <DialogTitle>{data ? 'Editar Banco' : 'Adicionar Banco'}</DialogTitle>
          <DialogDescription className="text-slate-400">
            Preencha os dados do banco
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="bank-name">Nome do Banco</Label>
            <Input
              id="bank-name"
              data-testid="bank-name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="bg-slate-950 border-slate-800 text-white"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="bank-status">Status</Label>
            <Select value={active.toString()} onValueChange={(v) => setActive(v === 'true')}>
              <SelectTrigger id="bank-status" data-testid="bank-status-select" className="bg-slate-950 border-slate-800 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800">
                <SelectItem value="true" className="text-white">Ativo</SelectItem>
                <SelectItem value="false" className="text-white">Inativo</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="text-slate-400">
              Cancelar
            </Button>
            <Button data-testid="save-bank-button" type="submit" className="bg-blue-600 hover:bg-blue-700">
              Salvar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function CategoryDialog({ open, data, onClose, onSave }) {
  const [name, setName] = useState('');
  const [type, setType] = useState('despesa');

  useEffect(() => {
    if (data) {
      setName(data.name);
      setType(data.type);
    } else {
      setName('');
      setType('despesa');
    }
  }, [data, open]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({ name, type });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-slate-900 border-slate-800 text-white">
        <DialogHeader>
          <DialogTitle>{data ? 'Editar Categoria' : 'Adicionar Categoria'}</DialogTitle>
          <DialogDescription className="text-slate-400">
            Preencha os dados da categoria
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="category-name">Nome da Categoria</Label>
            <Input
              id="category-name"
              data-testid="category-name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="bg-slate-950 border-slate-800 text-white"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="category-type">Tipo</Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger id="category-type" data-testid="category-type-select" className="bg-slate-950 border-slate-800 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800">
                <SelectItem value="receita" className="text-white">Receita</SelectItem>
                <SelectItem value="despesa" className="text-white">Despesa</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="text-slate-400">
              Cancelar
            </Button>
            <Button data-testid="save-category-button" type="submit" className="bg-blue-600 hover:bg-blue-700">
              Salvar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
