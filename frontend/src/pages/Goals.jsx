import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Target, Plus, TrendingUp, Calendar, DollarSign, Pencil, Trash2, Trophy, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../components/ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Goals() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialog, setDialog] = useState({ open: false, data: null });
  const [contributeDialog, setContributeDialog] = useState({ open: false, goalId: null });
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    target_amount: '',
    deadline: '',
    image_url: '',
    monthly_contribution: ''
  });
  const [contributeAmount, setContributeAmount] = useState('');

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchGoals();
  }, []);

  const fetchGoals = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/goals`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setGoals(response.data);
    } catch (error) {
      console.error('Error fetching goals:', error);
      toast.error('Erro ao carregar metas');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    
    try {
      const payload = {
        name: formData.name,
        description: formData.description || null,
        target_amount: parseFloat(formData.target_amount),
        deadline: formData.deadline ? new Date(formData.deadline).toISOString() : null,
        image_url: formData.image_url || null,
        monthly_contribution: parseFloat(formData.monthly_contribution) || 0
      };

      if (dialog.data) {
        await axios.put(`${API}/goals/${dialog.data.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success('Meta atualizada com sucesso!');
      } else {
        await axios.post(`${API}/goals`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success('Meta criada com sucesso!');
      }
      
      setDialog({ open: false, data: null });
      setFormData({ name: '', description: '', target_amount: '', deadline: '', image_url: '', monthly_contribution: '' });
      fetchGoals();
    } catch (error) {
      console.error('Error saving goal:', error);
      toast.error('Erro ao salvar meta');
    }
  };

  const handleContribute = async () => {
    if (!contributeAmount || parseFloat(contributeAmount) <= 0) {
      toast.error('Digite um valor válido');
      return;
    }

    try {
      await axios.post(
        `${API}/goals/${contributeDialog.goalId}/contribute`,
        { amount: parseFloat(contributeAmount) },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Contribuição adicionada!');
      setContributeDialog({ open: false, goalId: null });
      setContributeAmount('');
      fetchGoals();
    } catch (error) {
      console.error('Error contributing:', error);
      toast.error('Erro ao adicionar contribuição');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta meta?')) return;

    try {
      await axios.delete(`${API}/goals/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Meta excluída com sucesso');
      fetchGoals();
    } catch (error) {
      console.error('Error deleting goal:', error);
      toast.error('Erro ao excluir meta');
    }
  };

  const openEditDialog = (goal) => {
    setFormData({
      name: goal.name,
      description: goal.description || '',
      target_amount: goal.target_amount.toString(),
      deadline: goal.deadline ? new Date(goal.deadline).toISOString().split('T')[0] : '',
      image_url: goal.image_url || '',
      monthly_contribution: goal.monthly_contribution.toString()
    });
    setDialog({ open: true, data: goal });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  const calculateMonthsToGoal = (current, target, monthly) => {
    if (monthly <= 0) return null;
    const remaining = target - current;
    if (remaining <= 0) return 0;
    return Math.ceil(remaining / monthly);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Carregando metas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Metas Financeiras
          </h1>
          <p className="text-slate-400 text-lg">Defina e acompanhe suas conquistas</p>
        </div>

        <Button
          data-testid="add-goal-button"
          onClick={() => {
            setFormData({ name: '', description: '', target_amount: '', deadline: '', image_url: '', monthly_contribution: '' });
            setDialog({ open: true, data: null });
          }}
          className="bg-blue-600 hover:bg-blue-700 glow-blue button-glow"
        >
          <Plus className="w-5 h-5 mr-2" />
          Nova Meta
        </Button>
      </div>

      {goals.length === 0 ? (
        <Card className="glass-card border-slate-800">
          <CardContent className="py-12 text-center">
            <Target className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Nenhuma meta cadastrada</h3>
            <p className="text-slate-400 mb-4">Comece criando sua primeira meta financeira</p>
            <Button
              onClick={() => setDialog({ open: true, data: null })}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Criar Primeira Meta
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {goals.map((goal) => {
            const percentage = Math.min((goal.current_amount / goal.target_amount) * 100, 100);
            const remaining = goal.target_amount - goal.current_amount;
            const monthsToGoal = calculateMonthsToGoal(goal.current_amount, goal.target_amount, goal.monthly_contribution);
            const isCompleted = percentage >= 100;

            return (
              <Card
                key={goal.id}
                data-testid="goal-card"
                className={`card-hover ${isCompleted ? 'border-green-500/50 bg-gradient-to-br from-green-900/20 to-green-950/10' : 'glass-card border-slate-800'}`}
              >
                {goal.image_url && (
                  <div className="h-40 overflow-hidden rounded-t-xl">
                    <img
                      src={goal.image_url}
                      alt={goal.name}
                      className="w-full h-full object-cover"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  </div>
                )}
                
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-xl font-bold text-white flex items-center gap-2">
                        {isCompleted && <Trophy className="w-5 h-5 text-yellow-400" />}
                        {goal.name}
                      </CardTitle>
                      {goal.description && (
                        <CardDescription className="text-slate-400 mt-1">
                          {goal.description}
                        </CardDescription>
                      )}
                    </div>
                    <div className="flex gap-1">
                      <Button
                        data-testid="edit-goal-button"
                        size="sm"
                        variant="ghost"
                        onClick={() => openEditDialog(goal)}
                        className="text-blue-400 hover:text-blue-300 hover:bg-slate-800"
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        data-testid="delete-goal-button"
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(goal.id)}
                        className="text-red-400 hover:text-red-300 hover:bg-slate-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">Progresso</span>
                      <span className="text-white font-semibold">{percentage.toFixed(1)}%</span>
                    </div>
                    <Progress value={percentage} className="h-3" />
                    <div className="flex justify-between text-sm font-mono">
                      <span className="text-green-400">{formatCurrency(goal.current_amount)}</span>
                      <span className="text-slate-400">de</span>
                      <span className="text-blue-400">{formatCurrency(goal.target_amount)}</span>
                    </div>
                  </div>

                  {!isCompleted && remaining > 0 && (
                    <div className="bg-slate-950 rounded-lg p-3 space-y-2">
                      <div className="flex items-center gap-2 text-sm text-slate-300">
                        <AlertCircle className="w-4 h-4" />
                        <span>Faltam: {formatCurrency(remaining)}</span>
                      </div>
                      
                      {goal.monthly_contribution > 0 && monthsToGoal !== null && (
                        <div className="flex items-center gap-2 text-sm text-cyan-400">
                          <TrendingUp className="w-4 h-4" />
                          <span>
                            {monthsToGoal === 0 
                              ? 'Meta atingida!' 
                              : `Depositando ${formatCurrency(goal.monthly_contribution)}/mês → ${monthsToGoal} ${monthsToGoal === 1 ? 'mês' : 'meses'}`
                            }
                          </span>
                        </div>
                      )}

                      {goal.deadline && (
                        <div className="flex items-center gap-2 text-sm text-amber-400">
                          <Calendar className="w-4 h-4" />
                          <span>Prazo: {new Date(goal.deadline).toLocaleDateString('pt-BR')}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {isCompleted && (
                    <div className="bg-green-950/30 border border-green-500/30 rounded-lg p-3 text-center">
                      <Trophy className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                      <p className="text-green-400 font-semibold">🎉 Meta Atingida!</p>
                    </div>
                  )}

                  <Button
                    data-testid="contribute-button"
                    onClick={() => setContributeDialog({ open: true, goalId: goal.id })}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                    disabled={isCompleted}
                  >
                    <DollarSign className="w-4 h-4 mr-2" />
                    Adicionar Valor
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialog.open} onOpenChange={(open) => {
        setDialog({ open, data: null });
        setFormData({ name: '', description: '', target_amount: '', deadline: '', image_url: '', monthly_contribution: '' });
      }}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>{dialog.data ? 'Editar Meta' : 'Nova Meta'}</DialogTitle>
            <DialogDescription className="text-slate-400">
              Defina sua meta financeira e acompanhe o progresso
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSave} className="space-y-4">
            <div className="space-y-2">
              <Label>Nome da Meta*</Label>
              <Input
                data-testid="goal-name-input"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ex: Viagem para Europa, Carro Novo"
                required
                className="bg-slate-950 border-slate-800 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>Descrição</Label>
              <Input
                data-testid="goal-description-input"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Detalhes sobre a meta"
                className="bg-slate-950 border-slate-800 text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Valor Alvo*</Label>
                <Input
                  data-testid="goal-target-input"
                  type="number"
                  step="0.01"
                  value={formData.target_amount}
                  onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                  placeholder="10000.00"
                  required
                  className="bg-slate-950 border-slate-800 text-white"
                />
              </div>

              <div className="space-y-2">
                <Label>Contribuição Mensal</Label>
                <Input
                  data-testid="goal-monthly-input"
                  type="number"
                  step="0.01"
                  value={formData.monthly_contribution}
                  onChange={(e) => setFormData({ ...formData, monthly_contribution: e.target.value })}
                  placeholder="500.00"
                  className="bg-slate-950 border-slate-800 text-white"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Prazo (opcional)</Label>
              <Input
                data-testid="goal-deadline-input"
                type="date"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                className="bg-slate-950 border-slate-800 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label>URL da Imagem (opcional)</Label>
              <Input
                data-testid="goal-image-input"
                value={formData.image_url}
                onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                placeholder="https://exemplo.com/imagem.jpg"
                className="bg-slate-950 border-slate-800 text-white"
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setDialog({ open: false, data: null })}
                className="text-slate-400"
              >
                Cancelar
              </Button>
              <Button data-testid="save-goal-button" type="submit" className="bg-blue-600 hover:bg-blue-700">
                {dialog.data ? 'Salvar' : 'Criar Meta'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Contribute Dialog */}
      <Dialog open={contributeDialog.open} onOpenChange={(open) => {
        setContributeDialog({ open, goalId: null });
        setContributeAmount('');
      }}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle>Adicionar Contribuição</DialogTitle>
            <DialogDescription className="text-slate-400">
              Quanto você quer adicionar a esta meta?
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Valor</Label>
              <Input
                data-testid="contribute-amount-input"
                type="number"
                step="0.01"
                value={contributeAmount}
                onChange={(e) => setContributeAmount(e.target.value)}
                placeholder="100.00"
                className="bg-slate-950 border-slate-800 text-white"
                autoFocus
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setContributeDialog({ open: false, goalId: null });
                setContributeAmount('');
              }}
              className="text-slate-400"
            >
              Cancelar
            </Button>
            <Button
              data-testid="confirm-contribute-button"
              onClick={handleContribute}
              className="bg-purple-600 hover:bg-purple-700"
            >
              Adicionar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
