import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Trophy,
  Target,
  Heart,
  Flame,
  Star,
  Plus,
  X,
  Calendar,
  Gift,
  TrendingUp,
  Award,
  Zap,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Progress } from './ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from './ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Health Score Widget
export function HealthScoreWidget() {
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchScore();
  }, []);

  const fetchScore = async () => {
    try {
      const res = await axios.get(`${API}/gamification/health-score`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setScore(res.data);
    } catch (error) {
      console.error('Error fetching health score:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (level) => {
    switch (level) {
      case 'Excelente': return 'text-green-400';
      case 'Bom': return 'text-blue-400';
      case 'Atenção': return 'text-yellow-400';
      case 'Crítico': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  const getScoreGradient = (level) => {
    switch (level) {
      case 'Excelente': return 'from-green-500 to-emerald-600';
      case 'Bom': return 'from-blue-500 to-cyan-600';
      case 'Atenção': return 'from-yellow-500 to-orange-600';
      case 'Crítico': return 'from-red-500 to-rose-600';
      default: return 'from-slate-500 to-slate-600';
    }
  };

  const getProgressColor = (level) => {
    switch (level) {
      case 'Excelente': return 'bg-green-500';
      case 'Bom': return 'bg-blue-500';
      case 'Atenção': return 'bg-yellow-500';
      case 'Crítico': return 'bg-red-500';
      default: return 'bg-slate-500';
    }
  };

  if (loading) {
    return (
      <Card className="glass-card border-slate-800">
        <CardContent className="p-6">
          <div className="animate-pulse flex items-center gap-4">
            <div className="w-20 h-20 rounded-full bg-slate-700" />
            <div className="space-y-2 flex-1">
              <div className="h-4 bg-slate-700 rounded w-1/2" />
              <div className="h-3 bg-slate-700 rounded w-3/4" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!score) return null;

  return (
    <Card data-testid="health-score-card" className="glass-card border-slate-800 overflow-hidden">
      <div className={`h-1 bg-gradient-to-r ${getScoreGradient(score.level)}`} />
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-white text-lg">
          <Heart className={`w-5 h-5 ${getScoreColor(score.level)}`} />
          Saúde Financeira
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6">
          {/* Score Circle */}
          <div className="relative">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                className="text-slate-700"
              />
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="none"
                strokeDasharray={`${(score.total_score / 100) * 251.2} 251.2`}
                className={getScoreColor(score.level)}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center flex-col">
              <span className={`text-2xl font-bold ${getScoreColor(score.level)}`}>
                {score.total_score}
              </span>
              <span className="text-xs text-slate-400">de 100</span>
            </div>
          </div>

          {/* Score Details */}
          <div className="flex-1 space-y-3">
            <div className="flex items-center justify-between">
              <span className={`text-lg font-semibold ${getScoreColor(score.level)}`}>
                {score.level}
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 w-20">Reserva</span>
                <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className={getProgressColor(score.level)} 
                    style={{ width: `${(score.reserve_score / 30) * 100}%`, height: '100%' }}
                  />
                </div>
                <span className="text-slate-300 w-8 text-right">{score.reserve_score}/30</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 w-20">Despesas</span>
                <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className={getProgressColor(score.level)} 
                    style={{ width: `${(score.expense_ratio_score / 30) * 100}%`, height: '100%' }}
                  />
                </div>
                <span className="text-slate-300 w-8 text-right">{score.expense_ratio_score}/30</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 w-20">Constância</span>
                <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className={getProgressColor(score.level)} 
                    style={{ width: `${(score.consistency_score / 20) * 100}%`, height: '100%' }}
                  />
                </div>
                <span className="text-slate-300 w-8 text-right">{score.consistency_score}/20</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400 w-20">Metas</span>
                <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className={getProgressColor(score.level)} 
                    style={{ width: `${(score.goals_score / 20) * 100}%`, height: '100%' }}
                  />
                </div>
                <span className="text-slate-300 w-8 text-right">{score.goals_score}/20</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tips */}
        {score.tips && score.tips.length > 0 && (
          <div className="mt-4 space-y-1">
            {score.tips.map((tip, index) => (
              <p key={index} className="text-xs text-slate-400">{tip}</p>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Badges Widget
export function BadgesWidget() {
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newUnlocked, setNewUnlocked] = useState([]);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchBadges();
    checkNewBadges();
  }, []);

  const fetchBadges = async () => {
    try {
      const res = await axios.get(`${API}/gamification/badges`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setBadges(res.data);
    } catch (error) {
      console.error('Error fetching badges:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkNewBadges = async () => {
    try {
      const res = await axios.post(`${API}/gamification/check-badges`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.data.unlocked && res.data.unlocked.length > 0) {
        setNewUnlocked(res.data.unlocked);
        res.data.unlocked.forEach(badge => {
          toast.success(`🎉 Nova conquista: ${badge.name}!`, {
            description: 'Parabéns pelo seu progresso financeiro!',
            duration: 5000,
          });
        });
        fetchBadges(); // Refresh badges list
      }
    } catch (error) {
      console.error('Error checking badges:', error);
    }
  };

  if (loading) {
    return (
      <Card className="glass-card border-slate-800">
        <CardContent className="p-6">
          <div className="animate-pulse grid grid-cols-4 gap-3">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="w-12 h-12 rounded-full bg-slate-700" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const unlockedBadges = badges.filter(b => b.unlocked);
  const lockedBadges = badges.filter(b => !b.unlocked);

  return (
    <Card data-testid="badges-card" className="glass-card border-slate-800">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-white text-lg">
          <Trophy className="w-5 h-5 text-yellow-400" />
          Conquistas
          <span className="text-sm font-normal text-slate-400">
            ({unlockedBadges.length}/{badges.length})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-3">
          {badges.map((badge, index) => (
            <div
              key={index}
              className={`relative group flex flex-col items-center p-2 rounded-lg transition-all ${
                badge.unlocked 
                  ? 'bg-slate-800/50 hover:bg-slate-800' 
                  : 'bg-slate-900/50 opacity-40'
              }`}
              title={badge.description}
            >
              <span className="text-2xl">{badge.icon}</span>
              <span className="text-xs text-center text-slate-300 mt-1 line-clamp-1">
                {badge.name}
              </span>
              {!badge.unlocked && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-slate-500 text-lg">🔒</span>
                </div>
              )}
              {/* Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 rounded text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                {badge.description}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Family Challenges Widget
export function FamilyChallengesWidget() {
  const [challenges, setChallenges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [progressAmount, setProgressAmount] = useState('');
  const [newChallenge, setNewChallenge] = useState({
    name: '',
    description: '',
    target_amount: '',
    reward: '',
    deadline: '',
  });
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchChallenges();
  }, []);

  const fetchChallenges = async () => {
    try {
      const res = await axios.get(`${API}/gamification/challenges`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setChallenges(res.data);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  const createChallenge = async () => {
    if (!newChallenge.name || !newChallenge.target_amount || !newChallenge.reward) {
      toast.error('Preencha nome, meta e recompensa');
      return;
    }

    try {
      await axios.post(`${API}/gamification/challenges`, {
        ...newChallenge,
        target_amount: parseFloat(newChallenge.target_amount),
        deadline: newChallenge.deadline || null,
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Desafio criado com sucesso! 🎯');
      setShowCreateModal(false);
      setNewChallenge({ name: '', description: '', target_amount: '', reward: '', deadline: '' });
      fetchChallenges();
    } catch (error) {
      toast.error('Erro ao criar desafio');
    }
  };

  const updateProgress = async () => {
    if (!progressAmount || !selectedChallenge) return;

    try {
      const res = await axios.post(
        `${API}/gamification/challenges/${selectedChallenge.id}/progress?amount=${parseFloat(progressAmount)}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (res.data.is_completed) {
        toast.success(`🎉 Parabéns! Vocês completaram o desafio "${selectedChallenge.name}"!`, {
          description: `Recompensa: ${selectedChallenge.reward}`,
          duration: 8000,
        });
      } else {
        toast.success('Progresso atualizado!');
      }
      
      setShowProgressModal(false);
      setProgressAmount('');
      setSelectedChallenge(null);
      fetchChallenges();
    } catch (error) {
      toast.error('Erro ao atualizar progresso');
    }
  };

  const deleteChallenge = async (id) => {
    try {
      await axios.delete(`${API}/gamification/challenges/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success('Desafio removido');
      fetchChallenges();
    } catch (error) {
      toast.error('Erro ao remover desafio');
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const activeChallenge = challenges.find(c => c.is_active && !c.is_completed);

  if (loading) {
    return (
      <Card className="glass-card border-slate-800">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/2" />
            <div className="h-2 bg-slate-700 rounded w-full" />
            <div className="h-8 bg-slate-700 rounded w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card data-testid="challenges-card" className="glass-card border-slate-800 border-purple-500/30 bg-gradient-to-br from-purple-900/10 to-purple-950/5">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-white text-lg">
              <Target className="w-5 h-5 text-purple-400" />
              Desafio em Família
            </CardTitle>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setShowCreateModal(true)}
              className="text-purple-400 hover:text-purple-300 hover:bg-purple-900/20"
            >
              <Plus className="w-4 h-4 mr-1" />
              Novo
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {activeChallenge ? (
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-white font-medium">{activeChallenge.name}</h4>
                  <p className="text-sm text-slate-400">{activeChallenge.description}</p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => deleteChallenge(activeChallenge.id)}
                  className="text-slate-500 hover:text-red-400"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              {/* Progress */}
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Progresso</span>
                  <span className="text-purple-400 font-mono">
                    {formatCurrency(activeChallenge.current_amount || 0)} / {formatCurrency(activeChallenge.target_amount)}
                  </span>
                </div>
                <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                    style={{ 
                      width: `${Math.min(((activeChallenge.current_amount || 0) / activeChallenge.target_amount) * 100, 100)}%` 
                    }}
                  />
                </div>
              </div>

              {/* Reward */}
              <div className="flex items-center gap-2 text-sm">
                <Gift className="w-4 h-4 text-pink-400" />
                <span className="text-slate-300">Recompensa: {activeChallenge.reward}</span>
              </div>

              {/* Deadline */}
              {activeChallenge.deadline && (
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">
                    Até: {new Date(activeChallenge.deadline).toLocaleDateString('pt-BR')}
                  </span>
                </div>
              )}

              <Button
                onClick={() => {
                  setSelectedChallenge(activeChallenge);
                  setShowProgressModal(true);
                }}
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                <TrendingUp className="w-4 h-4 mr-2" />
                Registrar Economia
              </Button>
            </div>
          ) : (
            <div className="text-center py-6">
              <Flame className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 mb-3">Nenhum desafio ativo</p>
              <Button
                onClick={() => setShowCreateModal(true)}
                variant="outline"
                className="border-purple-500/50 text-purple-400 hover:bg-purple-900/20"
              >
                <Plus className="w-4 h-4 mr-2" />
                Criar Primeiro Desafio
              </Button>
            </div>
          )}

          {/* Completed Challenges */}
          {challenges.filter(c => c.is_completed).length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-700">
              <p className="text-xs text-slate-500 mb-2">
                ✅ {challenges.filter(c => c.is_completed).length} desafio(s) concluído(s)
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Challenge Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-400" />
              Novo Desafio em Família
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Crie um desafio de economia para toda a família participar
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Nome do Desafio</Label>
              <Input
                placeholder="Ex: Economizar na energia"
                value={newChallenge.name}
                onChange={(e) => setNewChallenge({...newChallenge, name: e.target.value})}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div>
              <Label>Descrição</Label>
              <Input
                placeholder="Ex: Reduzir conta de luz em R$ 200"
                value={newChallenge.description}
                onChange={(e) => setNewChallenge({...newChallenge, description: e.target.value})}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div>
              <Label>Meta de Economia (R$)</Label>
              <Input
                type="number"
                placeholder="200.00"
                value={newChallenge.target_amount}
                onChange={(e) => setNewChallenge({...newChallenge, target_amount: e.target.value})}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div>
              <Label>Recompensa</Label>
              <Input
                placeholder="Ex: Jantar especial em família"
                value={newChallenge.reward}
                onChange={(e) => setNewChallenge({...newChallenge, reward: e.target.value})}
                className="bg-slate-800 border-slate-700"
              />
            </div>
            <div>
              <Label>Prazo (opcional)</Label>
              <Input
                type="date"
                value={newChallenge.deadline}
                onChange={(e) => setNewChallenge({...newChallenge, deadline: e.target.value})}
                className="bg-slate-800 border-slate-700"
              />
            </div>
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button variant="ghost" className="text-slate-400">Cancelar</Button>
            </DialogClose>
            <Button onClick={createChallenge} className="bg-purple-600 hover:bg-purple-700">
              Criar Desafio
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Update Progress Modal */}
      <Dialog open={showProgressModal} onOpenChange={setShowProgressModal}>
        <DialogContent className="bg-slate-900 border-slate-800 text-white">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-400" />
              Registrar Economia
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Quanto vocês economizaram no desafio "{selectedChallenge?.name}"?
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Valor Economizado (R$)</Label>
              <Input
                type="number"
                placeholder="50.00"
                value={progressAmount}
                onChange={(e) => setProgressAmount(e.target.value)}
                className="bg-slate-800 border-slate-700"
              />
            </div>
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button variant="ghost" className="text-slate-400">Cancelar</Button>
            </DialogClose>
            <Button onClick={updateProgress} className="bg-purple-600 hover:bg-purple-700">
              Registrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Combined Gamification Section for Dashboard
export default function GamificationSection() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-6 h-6 text-yellow-400" />
        <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
          Gamificação & Motivação
        </h2>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <HealthScoreWidget />
        <BadgesWidget />
        <FamilyChallengesWidget />
      </div>
    </div>
  );
}
