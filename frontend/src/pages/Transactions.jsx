import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Search,
  Filter,
  Pencil,
  Trash2,
  Calendar,
  DollarSign,
  Tag,
  User,
  Building2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
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

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [filteredTransactions, setFilteredTransactions] = useState([]);
  const [members, setMembers] = useState([]);
  const [banks, setBanks] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [editDialog, setEditDialog] = useState({ open: false, data: null });
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkCategoryDialog, setBulkCategoryDialog] = useState(false);
  const [bulkCategoryId, setBulkCategoryId] = useState('');

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    filterTransactions();
  }, [transactions, searchTerm, filterType]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [transRes, membersRes, banksRes, categoriesRes] = await Promise.all([
        axios.get(`${API}/transactions`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/family`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/banks`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/categories`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setTransactions(transRes.data);
      setMembers(membersRes.data);
      setBanks(banksRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erro ao carregar transações');
    } finally {
      setLoading(false);
    }
  };

  const filterTransactions = () => {
    let filtered = transactions;

    if (searchTerm) {
      filtered = filtered.filter((t) =>
        t.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterType !== 'all') {
      filtered = filtered.filter((t) => t.type === filterType);
    }

    setFilteredTransactions(filtered);
  };

  const handleEdit = async (updatedData) => {
    try {
      await axios.put(
        `${API}/transactions/${editDialog.data.id}`,
        {
          date: new Date(updatedData.date).toISOString(),
          description: updatedData.description,
          amount: parseFloat(updatedData.amount),
          type: updatedData.type,
          category_id: updatedData.category_id || null,
          member_id: updatedData.member_id,
          bank_id: updatedData.bank_id,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Transação atualizada com sucesso');
      fetchData();
      setEditDialog({ open: false, data: null });
    } catch (error) {
      console.error('Error updating transaction:', error);
      toast.error('Erro ao atualizar transação');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta transação?')) return;

    try {
      await axios.delete(`${API}/transactions/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      toast.success('Transação excluída com sucesso');
      fetchData();
    } catch (error) {
      console.error('Error deleting transaction:', error);
      toast.error('Erro ao excluir transação');
    }
  };

  const handleSelectAll = () => {
    if (selectedIds.length === filteredTransactions.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredTransactions.map((t) => t.id));
    }
  };

  const handleSelectOne = (id) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((sid) => sid !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleBulkCategorize = async () => {
    if (!bulkCategoryId || selectedIds.length === 0) {
      toast.error('Selecione uma categoria');
      return;
    }

    try {
      const response = await axios.post(
        `${API}/transactions/bulk-categorize`,
        {
          transaction_ids: selectedIds,
          category_id: bulkCategoryId,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success(`${response.data.count} transações categorizadas com sucesso!`);
      setSelectedIds([]);
      setBulkCategoryDialog(false);
      setBulkCategoryId('');
      fetchData();
    } catch (error) {
      console.error('Error bulk categorizing:', error);
      toast.error('Erro ao categorizar transações');
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('pt-BR');
  };

  const getMemberName = (id) => members.find((m) => m.id === id)?.name || 'N/A';
  const getBankName = (id) => banks.find((b) => b.id === id)?.name || 'N/A';
  const getCategoryName = (id) =>
    id ? categories.find((c) => c.id === id)?.name || 'Sem categoria' : 'Sem categoria';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Carregando transações...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1
          className="text-4xl md:text-5xl font-bold text-white mb-2"
          style={{ fontFamily: 'Manrope, sans-serif' }}
        >
          Transações
        </h1>
        <p className="text-slate-400 text-lg">
          Gerencie e categorize suas transações importadas
        </p>
      </div>

      {/* Filters */}
      <Card className="glass-card border-slate-800">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              <Input
                data-testid="search-transactions"
                placeholder="Buscar por descrição..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-slate-950 border-slate-800 text-white pl-11"
              />
            </div>

            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-slate-400" />
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger data-testid="filter-type" className="w-[180px] bg-slate-950 border-slate-800 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  <SelectItem value="all" className="text-white">Todas</SelectItem>
                  <SelectItem value="receita" className="text-white">Receitas</SelectItem>
                  <SelectItem value="despesa" className="text-white">Despesas</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass-card border-slate-800">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-400 mb-1">Total de Transações</p>
            <p className="text-3xl font-bold text-white font-mono">{filteredTransactions.length}</p>
          </CardContent>
        </Card>
        <Card className="glass-card border-slate-800">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-400 mb-1">Receitas</p>
            <p className="text-3xl font-bold text-green-400 font-mono">
              {filteredTransactions.filter((t) => t.type === 'receita').length}
            </p>
          </CardContent>
        </Card>
        <Card className="glass-card border-slate-800">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-400 mb-1">Despesas</p>
            <p className="text-3xl font-bold text-red-400 font-mono">
              {filteredTransactions.filter((t) => t.type === 'despesa').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Transactions List */}
      <Card className="solid-card border-slate-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl font-bold text-white">
              Lista de Transações ({filteredTransactions.length})
            </CardTitle>
            {selectedIds.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-slate-400">
                  {selectedIds.length} selecionada(s)
                </span>
                <Button
                  data-testid="bulk-categorize-button"
                  onClick={() => setBulkCategoryDialog(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                  size="sm"
                >
                  <Tag className="w-4 h-4 mr-2" />
                  Categorizar Selecionadas
                </Button>
                <Button
                  onClick={() => setSelectedIds([])}
                  variant="ghost"
                  size="sm"
                  className="text-slate-400"
                >
                  Limpar
                </Button>
              </div>
            )}
          </div>
          {filteredTransactions.length > 0 && (
            <div className="flex items-center gap-2 mt-2">
              <input
                type="checkbox"
                data-testid="select-all-checkbox"
                checked={selectedIds.length === filteredTransactions.length && filteredTransactions.length > 0}
                onChange={handleSelectAll}
                className="w-4 h-4 rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-blue-500"
              />
              <label className="text-sm text-slate-400 cursor-pointer" onClick={handleSelectAll}>
                Selecionar todas
              </label>
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredTransactions.length > 0 ? (
              filteredTransactions.map((transaction) => (
                <div
                  key={transaction.id}
                  data-testid="transaction-item"
                  className={`glass-card p-4 rounded-xl border-slate-800 hover:border-blue-500/30 transition-all ${
                    selectedIds.includes(transaction.id) ? 'ring-2 ring-blue-500 border-blue-500' : ''
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <input
                      type="checkbox"
                      data-testid="transaction-checkbox"
                      checked={selectedIds.includes(transaction.id)}
                      onChange={() => handleSelectOne(transaction.id)}
                      className="mt-1 w-5 h-5 rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">\n                        <div className="flex-1 space-y-2">\n                          <div className="flex items-center gap-3">\n                            <h3 className="text-lg font-semibold text-white">\n                              {transaction.description}\n                            </h3>\n                            <span\n                              className={`px-3 py-1 rounded-full text-xs font-semibold ${\n                                transaction.type === 'receita'\n                                  ? 'bg-green-500/20 text-green-400'\n                                  : 'bg-red-500/20 text-red-400'\n                              }`}\n                            >\n                              {transaction.type === 'receita' ? 'Receita' : 'Despesa'}\n                            </span>\n                          </div>\n\n                          <div className="flex flex-wrap gap-4 text-sm text-slate-400">\n                            <div className="flex items-center gap-2">\n                              <Calendar className="w-4 h-4" />\n                              {formatDate(transaction.date)}\n                            </div>\n                            <div className="flex items-center gap-2">\n                              <User className="w-4 h-4" />\n                              {getMemberName(transaction.member_id)}\n                            </div>\n                            <div className="flex items-center gap-2">\n                              <Building2 className="w-4 h-4" />\n                              {getBankName(transaction.bank_id)}\n                            </div>\n                            <div className="flex items-center gap-2">\n                              <Tag className="w-4 h-4" />\n                              {getCategoryName(transaction.category_id)}\n                            </div>\n                          </div>\n                        </div>\n\n                        <div className="flex items-center gap-4">\n                          <p\n                            className={`text-2xl font-bold font-mono ${\n                              transaction.type === 'receita' ? 'text-green-400' : 'text-red-400'\n                            }`}\n                          >\n                            {formatCurrency(transaction.amount)}\n                          </p>\n\n                          <div className="flex gap-2">\n                            <Button\n                              data-testid="edit-transaction-button"\n                              size="sm"\n                              variant="ghost"\n                              onClick={() => setEditDialog({ open: true, data: transaction })}\n                              className="text-blue-400 hover:text-blue-300 hover:bg-slate-800"\n                            >\n                              <Pencil className="w-4 h-4" />\n                            </Button>\n                            <Button\n                              data-testid="delete-transaction-button"\n                              size="sm"\n                              variant="ghost"\n                              onClick={() => handleDelete(transaction.id)}\n                              className="text-red-400 hover:text-red-300 hover:bg-slate-800"\n                            >\n                              <Trash2 className="w-4 h-4" />\n                            </Button>\n                          </div>\n                        </div>\n                      </div>\n                    </div>\n                  </div>\n                </div>\n              ))\n            ) : (
              <div className="py-12 text-center text-slate-500">
                {searchTerm || filterType !== 'all'
                  ? 'Nenhuma transação encontrada com os filtros aplicados'
                  : 'Nenhuma transação encontrada. Importe extratos para começar.'}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <EditTransactionDialog
        open={editDialog.open}
        data={editDialog.data}
        members={members}
        banks={banks}
        categories={categories}
        onClose={() => setEditDialog({ open: false, data: null })}
        onSave={handleEdit}
      />

      {/* Bulk Categorize Dialog */}
      <Dialog open={bulkCategoryDialog} onOpenChange={setBulkCategoryDialog}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle>Categorizar {selectedIds.length} Transações</DialogTitle>
            <DialogDescription className="text-slate-400">
              Selecione uma categoria para aplicar às transações selecionadas
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Categoria</Label>
              <Select value={bulkCategoryId} onValueChange={setBulkCategoryId}>
                <SelectTrigger data-testid="bulk-category-select" className="bg-slate-950 border-slate-800 text-white">
                  <SelectValue placeholder="Selecione uma categoria" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  {categories.map((cat) => (
                    <SelectItem key={cat.id} value={cat.id} className="text-white">
                      {cat.name} ({cat.type === 'especial' ? 'Especial' : cat.type})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setBulkCategoryDialog(false);
                setBulkCategoryId('');
              }}
              className="text-slate-400"
            >
              Cancelar
            </Button>
            <Button
              data-testid="confirm-bulk-categorize"
              onClick={handleBulkCategorize}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Categorizar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function EditTransactionDialog({ open, data, members, banks, categories, onClose, onSave }) {
  const [formData, setFormData] = useState({
    date: '',
    description: '',
    amount: '',
    type: 'despesa',
    category_id: '',
    member_id: '',
    bank_id: '',
  });

  useEffect(() => {
    if (data) {
      setFormData({
        date: new Date(data.date).toISOString().split('T')[0],
        description: data.description,
        amount: data.amount.toString(),
        type: data.type,
        category_id: data.category_id || '',
        member_id: data.member_id,
        bank_id: data.bank_id,
      });
    }
  }, [data, open]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-slate-900 border-slate-800 text-white max-w-2xl">
        <DialogHeader>
          <DialogTitle>Editar Transação</DialogTitle>
          <DialogDescription className="text-slate-400">
            Atualize os dados da transação e categorize conforme necessário
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Data</Label>
              <Input
                data-testid="edit-date-input"
                type="date"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
                className="bg-slate-950 border-slate-800 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Select value={formData.type} onValueChange={(v) => setFormData({ ...formData, type: v })}>
                <SelectTrigger data-testid="edit-type-select" className="bg-slate-950 border-slate-800 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  <SelectItem value="receita" className="text-white">Receita</SelectItem>
                  <SelectItem value="despesa" className="text-white">Despesa</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Descrição</Label>
            <Input
              data-testid="edit-description-input"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
              className="bg-slate-950 border-slate-800 text-white"
            />
          </div>

          <div className="space-y-2">
            <Label>Valor</Label>
            <Input
              data-testid="edit-amount-input"
              type="number"
              step="0.01"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              required
              className="bg-slate-950 border-slate-800 text-white"
            />
          </div>

          <div className="space-y-2">
            <Label>Categoria</Label>
            <Select
              value={formData.category_id}
              onValueChange={(v) => setFormData({ ...formData, category_id: v })}
            >
              <SelectTrigger data-testid="edit-category-select" className="bg-slate-950 border-slate-800 text-white">
                <SelectValue placeholder="Selecione uma categoria" />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800">
                <SelectItem value="" className="text-white">Sem categoria</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id} className="text-white">
                    {cat.name} ({cat.type})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Membro</Label>
              <Select
                value={formData.member_id}
                onValueChange={(v) => setFormData({ ...formData, member_id: v })}
              >
                <SelectTrigger data-testid="edit-member-select" className="bg-slate-950 border-slate-800 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  {members.map((member) => (
                    <SelectItem key={member.id} value={member.id} className="text-white">
                      {member.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Banco</Label>
              <Select
                value={formData.bank_id}
                onValueChange={(v) => setFormData({ ...formData, bank_id: v })}
              >
                <SelectTrigger data-testid="edit-bank-select" className="bg-slate-950 border-slate-800 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  {banks.map((bank) => (
                    <SelectItem key={bank.id} value={bank.id} className="text-white">
                      {bank.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="text-slate-400">
              Cancelar
            </Button>
            <Button data-testid="save-edit-button" type="submit" className="bg-blue-600 hover:bg-blue-700">
              Salvar Alterações
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
